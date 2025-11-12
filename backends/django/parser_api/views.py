import os
import sys
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, FileResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ProcessingSession, UploadedFile, Transaction, Category, TransactionPattern
from .serializers import ProcessingSessionSerializer

sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'src'))
from parsers.parser_factory import ParserFactory
from utils.pdf_processor import PDFProcessor

channel_layer = get_channel_layer()


def save_transactions_to_db(transactions, session, uploaded_file):
    """
    Save extracted transactions to the database
    """
    saved_transactions = []
    for transaction_data in transactions:
        try:
            transaction = Transaction.objects.create(
                session=session,
                uploaded_file=uploaded_file,
                date=transaction_data.get('Date'),
                description=transaction_data.get('Description', ''),
                original_description=transaction_data.get('Original Description', ''),
                amount=transaction_data.get('Amount', 0),
                transaction_type=transaction_data.get('Transaction Type', ''),
                account_name=transaction_data.get('Account Name', ''),
                account_holder='default',
                bank_type=uploaded_file.bank_type,
                account_type=uploaded_file.account_type,
            )
            
            # Try to auto-categorize the transaction
            auto_categorize_transaction(transaction)
            saved_transactions.append(transaction)
            
        except Exception as e:
            print(f"Error saving transaction: {e}")
            continue
    
    return saved_transactions


def auto_categorize_transaction(transaction):
    """
    Automatically categorize a transaction based on existing patterns
    """
    description = transaction.description.lower()
    
    # Find matching patterns ordered by confidence
    patterns = TransactionPattern.objects.filter(is_active=True).order_by('-confidence')
    
    for pattern in patterns:
        pattern_text = pattern.pattern.lower()
        match_found = False
        
        if pattern.match_type == 'exact':
            match_found = description == pattern_text
        elif pattern.match_type == 'contains':
            match_found = pattern_text in description
        elif pattern.match_type == 'starts_with':
            match_found = description.startswith(pattern_text)
        elif pattern.match_type == 'ends_with':
            match_found = description.endswith(pattern_text)
        elif pattern.match_type == 'regex':
            import re
            try:
                match_found = bool(re.search(pattern_text, description))
            except re.error:
                continue
        
        if match_found:
            transaction.category = pattern.category
            transaction.category_confidence = pattern.confidence
            transaction.save()
            break


def detect_parser_type(text_content, filename=None):
    """
    Auto-detect bank and account type from PDF text content and filename
    Returns: (bank_type, account_type)
    """
    filename_lower = filename.lower() if filename else ''
    
    # PRIMARY: Exact filename pattern matching (highest priority)
    filename_patterns = [
        ('gyt credit', ('gyt', 'credit')),
        ('bi checking gtq', ('industrial', 'checking')),
        ('bi checking usd', ('industrial', 'usd_checking')),
        ('bi credit gtq', ('industrial', 'credit')),
        ('bi credit usd', ('industrial', 'credit_usd')),
        ('bam credit', ('bam', 'credit')),
    ]
    
    for pattern, (bank_type, account_type) in filename_patterns:
        if pattern in filename_lower:
            return (bank_type, account_type)
    
    # SECONDARY: Fallback to content + filename analysis
    text_lower = text_content.lower()
    combined_content = text_lower + ' ' + filename_lower
    
    # Enhanced detection patterns with filename support
    
    # Banco Industrial detection
    industrial_keywords = ['banco industrial', 'industrial', 'bi']
    if any(keyword in combined_content for keyword in industrial_keywords):
        
        # Credit card detection
        credit_keywords = ['tarjeta de credito', 'credit card', 'tarjeta', 'credit', 'tc', 'credito']
        if any(keyword in combined_content for keyword in credit_keywords):
            # Check for USD
            usd_keywords = ['$', 'usd', 'dolar', 'dollar', 'dolares']
            if any(keyword in combined_content for keyword in usd_keywords):
                return ('industrial', 'credit_usd')
            return ('industrial', 'credit')
        
        # Checking account detection
        checking_keywords = ['cuenta corriente', 'checking', 'corriente', 'monetaria', 'ahorro']
        if any(keyword in combined_content for keyword in checking_keywords):
            # Check for USD
            usd_keywords = ['$', 'usd', 'dolar', 'dollar', 'dolares']
            if any(keyword in combined_content for keyword in usd_keywords):
                return ('industrial', 'usd_checking')
            return ('industrial', 'checking')
        
        # Default to checking if Industrial but no specific type found
        # Check for USD in this case too
        usd_keywords = ['$', 'usd', 'dolar', 'dollar', 'dolares']
        if any(keyword in combined_content for keyword in usd_keywords):
            return ('industrial', 'usd_checking')
        return ('industrial', 'checking')
    
    # BAM detection
    bam_keywords = ['bam', 'banco agromercantil', 'agromercantil']
    if any(keyword in combined_content for keyword in bam_keywords):
        # BAM typically only has credit cards in our system
        return ('bam', 'credit')
    
    # GyT detection  
    gyt_keywords = ['gyt', 'g&t', 'gyp', 'g y t', 'continental']
    if any(keyword in combined_content for keyword in gyt_keywords):
        # GyT typically only has credit cards in our system
        return ('gyt', 'credit')
    
    return (None, None)


def validate_csv_file(file_path):
    """
    Validate that CSV file has the expected Banco Industrial format
    Raises ValueError if validation fails
    """
    import pandas as pd
    import re

    try:
        # Try multiple encodings
        encodings = ['utf-8', 'utf-16-be', 'utf-16-le', 'latin-1', 'cp1252']
        lines = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    test_lines = f.readlines()
                    # Check if readable
                    if any('Fecha' in line or 'fecha' in line.lower() for line in test_lines[:15]):
                        lines = test_lines
                        print(f"Validating CSV with encoding: {encoding}")
                        break
            except:
                continue

        if not lines:
            raise ValueError("Could not read CSV file with any known encoding")

        if len(lines) < 10:
            raise ValueError("CSV file is too short - expected at least 10 lines of header + data")

        # Find header line (should contain Fecha, TT, Descripción)
        header_found = False
        for line in lines[:15]:
            if 'Fecha' in line and 'TT' in line and 'Descripci' in line:
                header_found = True
                # Validate key columns
                if 'Debe' not in line or 'Haber' not in line:
                    raise ValueError("Missing required columns: Debe or Haber")
                break

        if not header_found:
            raise ValueError("Invalid CSV format: Could not find header row with 'Fecha,TT,Descripción'")

        # Check for date range line
        date_range_found = False
        for line in lines[:10]:
            if re.search(r'Del\s+\d{2}/\d{2}/\d{4}\s+al\s+\d{2}/\d{2}/\d{4}', line):
                date_range_found = True
                break

        if not date_range_found:
            raise ValueError("Invalid CSV format: Missing date range line (Del DD/MM/YYYY al DD/MM/YYYY)")

        return True

    except Exception as e:
        raise ValueError(f"CSV validation failed: {str(e)}")


def detect_csv_bank_type(file_path):
    """
    Auto-detect bank and account type from CSV file structure and content
    Returns: (bank_type, account_type)
    """
    try:
        # Try multiple encodings (CSV files can be UTF-8, UTF-16, etc.)
        encodings = ['utf-8', 'utf-16-be', 'utf-16-le', 'latin-1', 'cp1252']
        content = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    test_content = f.read().lower()
                    # Check if this encoding produces readable content
                    if 'fecha' in test_content and 'tt' in test_content:
                        content = test_content
                        print(f"Successfully read CSV with encoding: {encoding}")
                        break
            except:
                continue

        if not content:
            print("Could not read CSV file with any known encoding")
            return (None, None)

        # Check if it's Banco Industrial format
        # BI CSVs have specific header structure with TT, Debe, Haber columns
        has_bi_structure = all(keyword in content for keyword in ['fecha', 'tt', 'debe', 'haber', 'saldo'])

        if not has_bi_structure:
            return (None, None)

        # Detect currency - USD vs GTQ
        # Look for USD indicators in column headers or content
        usd_indicators = ['debe (usd)', 'haber (usd)', 'debe ($)', 'haber ($)', 'saldo (usd)', 'saldo ($)']
        gtq_indicators = ['debe (q.)', 'haber (q.)', 'saldo (q.)']

        is_usd = any(indicator in content for indicator in usd_indicators)
        is_gtq = any(indicator in content for indicator in gtq_indicators)

        # BI CSV formats are only for checking accounts (not credit cards)
        if is_usd:
            return ('industrial', 'usd_checking')
        elif is_gtq or has_bi_structure:  # Default to GTQ if BI structure found
            return ('industrial', 'checking')

        return (None, None)

    except Exception as e:
        print(f"Error detecting CSV type: {e}")
        return (None, None)


def send_websocket_update(session_id, data):
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f"session_{session_id}",
                {
                    "type": "progress_update",
                    "data": data
                }
            )
        except Exception as e:
            print(f"WebSocket update failed: {e}")
            pass


@api_view(['POST'])
def upload_files(request):
    files = request.FILES.getlist('files')
    if not files:
        return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get parser selections from request
    parsers_data = request.POST.get('parsers', '{}')
    
    try:
        import json
        parsers = json.loads(parsers_data) if parsers_data else {}
    except json.JSONDecodeError:
        parsers = {}
    
    session = ProcessingSession.objects.create(
        total_files=len(files),
        status='uploading'
    )
    
    session_dir = settings.TEMP_UPLOAD_DIR / str(session.session_id)
    session_dir.mkdir(exist_ok=True)
    
    uploaded_files = []
    for file in files:
        file_path = session_dir / file.name
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Detect file type from extension
        file_extension = file.name.lower().split('.')[-1]
        if file_extension == 'pdf':
            file_type = 'pdf'
        elif file_extension == 'csv':
            file_type = 'csv'
        else:
            # Default to pdf for backwards compatibility
            file_type = 'pdf'

        # Get parser info for this file
        parser_info = parsers.get(file.name, {})

        uploaded_file = UploadedFile.objects.create(
            session=session,
            filename=file.name,
            file_path=str(file_path),
            file_type=file_type,
            bank_type=parser_info.get('bank', ''),
            account_type=parser_info.get('account', ''),
            account_holder='default'  # Set default value since we're removing this functionality
        )
        uploaded_files.append(uploaded_file)
    
    session.status = 'ready'
    session.save()
    
    serializer = ProcessingSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def update_parser_selections(request, session_id):
    """Update parser selections for uploaded files in a session"""
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    parsers_data = request.data.get('parsers', {})
    print(f"Updating parser selections for session {session_id}: {parsers_data}")
    
    # Update parser info for each file
    for uploaded_file in session.files.all():
        parser_info = parsers_data.get(uploaded_file.filename, {})
        if parser_info:
            uploaded_file.bank_type = parser_info.get('bank', '')
            uploaded_file.account_type = parser_info.get('account', '')
            uploaded_file.save()
            print(f"Updated {uploaded_file.filename}: {uploaded_file.bank_type} {uploaded_file.account_type}")
    
    return Response({'message': 'Parser selections updated'})


@api_view(['POST'])
def process_files(request, session_id):
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if session.status != 'ready':
        return Response({'error': 'Session not ready for processing'}, status=status.HTTP_400_BAD_REQUEST)
    
    session.status = 'processing'
    session.save()
    
    send_websocket_update(session_id, {
        'type': 'status_update',
        'status': 'processing',
        'message': 'Starting processing...'
    })
    
    all_transactions = []
    pdf_processor = PDFProcessor()
    
    for uploaded_file in session.files.all():
        try:
            send_websocket_update(session_id, {
                'type': 'file_processing',
                'filename': uploaded_file.filename,
                'message': f'Processing {uploaded_file.filename}...'
            })

            # Get parser info from uploaded file record
            print(f"Processing file: {uploaded_file.filename}")
            print(f"File type: {uploaded_file.file_type}")
            print(f"Bank type: {uploaded_file.bank_type}, Account type: {uploaded_file.account_type}")

            # Branch processing based on file type
            if uploaded_file.file_type == 'csv':
                # CSV processing path
                try:
                    # Validate CSV format
                    validate_csv_file(uploaded_file.file_path)
                    print(f"CSV file {uploaded_file.filename} validated successfully")
                except ValueError as ve:
                    uploaded_file.status = 'error'
                    uploaded_file.error_message = f'CSV validation failed: {str(ve)}'
                    uploaded_file.save()
                    print(f"CSV validation error for {uploaded_file.filename}: {str(ve)}")
                    continue

                # Auto-detect if not specified
                if not uploaded_file.bank_type or not uploaded_file.account_type:
                    detected_bank, detected_account = detect_csv_bank_type(uploaded_file.file_path)
                    if detected_bank and detected_account:
                        uploaded_file.bank_type = detected_bank
                        uploaded_file.account_type = detected_account
                        uploaded_file.save()
                        print(f"Auto-detected CSV parser: {detected_bank} {detected_account}")
                    else:
                        uploaded_file.status = 'error'
                        uploaded_file.error_message = 'Could not auto-detect parser type for CSV file'
                        uploaded_file.save()
                        print(f"Skipping {uploaded_file.filename} - could not detect parser type")
                        continue

                # Get CSV parser
                parser = ParserFactory.get_csv_parser(
                    bank_type=uploaded_file.bank_type,
                    account_type=uploaded_file.account_type,
                    csv_path=uploaded_file.file_path,
                    is_spouse=False
                )

            else:
                # PDF processing path (existing logic)
                text_content = pdf_processor.process(uploaded_file.file_path)
                if not text_content.strip():
                    uploaded_file.status = 'error'
                    uploaded_file.error_message = 'No text content extracted from PDF'
                    uploaded_file.save()
                    continue

                if not uploaded_file.bank_type or not uploaded_file.account_type:
                    uploaded_file.status = 'error'
                    uploaded_file.error_message = 'No parser type specified for this file'
                    uploaded_file.save()
                    print(f"Skipping {uploaded_file.filename} - no parser type specified")
                    continue

                parser = ParserFactory.get_parser(
                    bank_type=uploaded_file.bank_type,
                    account_type=uploaded_file.account_type,
                    pdf_path=uploaded_file.file_path,
                    is_spouse=False  # Always False since we're removing spouse functionality
                )
            
            print(f"Extracting data from {uploaded_file.filename} using {uploaded_file.bank_type} {uploaded_file.account_type} parser...")
            transactions = parser.extract_data()
            print(f"Extracted {len(transactions) if transactions else 0} transactions from {uploaded_file.filename}")
            
            if transactions:
                # Update Account Name to include filename
                for transaction in transactions:
                    original_account_name = transaction.get('Account Name', '')
                    transaction['Account Name'] = f"{original_account_name} - {uploaded_file.filename}"
                
                # Save transactions to database
                saved_transactions = save_transactions_to_db(transactions, session, uploaded_file)
                all_transactions.extend(transactions)  # Keep for CSV export
                print(f"Added {len(transactions)} transactions to total (now {len(all_transactions)})")
                
                uploaded_file.status = 'completed'
                uploaded_file.processed_at = datetime.now()
                
                send_websocket_update(session_id, {
                    'type': 'transactions_saved',
                    'filename': uploaded_file.filename,
                    'count': len(saved_transactions),
                    'message': f'Saved {len(saved_transactions)} transactions to database'
                })
            else:
                uploaded_file.status = 'error'
                uploaded_file.error_message = 'No transactions extracted'
            
            uploaded_file.save()
            session.processed_files += 1
            session.save()
            
            send_websocket_update(session_id, {
                'type': 'progress_update',
                'processed': session.processed_files,
                'total': session.total_files,
                'filename': uploaded_file.filename,
                'status': uploaded_file.status
            })
            
        except Exception as e:
            uploaded_file.status = 'error'
            uploaded_file.error_message = str(e)
            uploaded_file.save()
            
            send_websocket_update(session_id, {
                'type': 'file_error',
                'filename': uploaded_file.filename,
                'error': str(e)
            })
    
    print(f"Total transactions collected: {len(all_transactions)}")
    
    if all_transactions:
        output_filename = f"all_transactions_{session_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        output_path = settings.TEMP_OUTPUT_DIR / output_filename
        
        import pandas as pd
        df = pd.DataFrame(all_transactions)
        df.to_csv(output_path, index=False)
        
        session.output_file = output_filename
        session.status = 'completed'
        print(f"Processing completed successfully. Output file: {output_filename}")
    else:
        session.status = 'error'
        print("No transactions were extracted from any files")
    
    session.save()
    
    send_websocket_update(session_id, {
        'type': 'processing_complete',
        'status': session.status,
        'output_file': session.output_file if session.output_file else None,
        'message': 'Processing completed!'
    })
    
    serializer = ProcessingSessionSerializer(session)
    return Response(serializer.data)


@api_view(['GET'])
def download_file(request, session_id):
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not session.output_file:
        return Response({'error': 'No output file available'}, status=status.HTTP_404_NOT_FOUND)
    
    file_path = settings.TEMP_OUTPUT_DIR / session.output_file
    if not file_path.exists():
        return Response({'error': 'Output file not found'}, status=status.HTTP_404_NOT_FOUND)
    
    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=session.output_file
    )
    return response


@api_view(['GET'])
def get_session_status(request, session_id):
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
        serializer = ProcessingSessionSerializer(session)
        return Response(serializer.data)
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def cleanup_session(request, session_id):
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
        
        session_dir = settings.TEMP_UPLOAD_DIR / str(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
        
        if session.output_file:
            output_path = settings.TEMP_OUTPUT_DIR / session.output_file
            if output_path.exists():
                output_path.unlink()
        
        session.delete()
        return Response({'message': 'Session cleaned up successfully'})
        
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def detect_parser_types(request, session_id):
    """Auto-detect parser types for uploaded files in a session"""
    try:
        session = ProcessingSession.objects.get(session_id=session_id)
    except ProcessingSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    pdf_processor = PDFProcessor()
    results = {}
    
    for uploaded_file in session.files.all():
        try:
            # Branch based on file type
            if uploaded_file.file_type == 'csv':
                # CSV auto-detection
                bank_type, account_type = detect_csv_bank_type(uploaded_file.file_path)

                if not bank_type or not account_type:
                    results[uploaded_file.filename] = {
                        'suggested': None,
                        'confidence': 0,
                        'error': 'Could not detect parser type from CSV structure'
                    }
                    continue
            else:
                # PDF auto-detection (existing logic)
                # Extract text from PDF
                text_content = pdf_processor.process(uploaded_file.file_path)
                if not text_content.strip():
                    results[uploaded_file.filename] = {
                        'suggested': None,
                        'confidence': 0,
                        'error': 'No text content extracted from PDF'
                    }
                    continue

                # Detect parser type (pass filename for enhanced detection)
                bank_type, account_type = detect_parser_type(text_content, uploaded_file.filename)
            
            if bank_type and account_type:
                # Find matching parser info
                parser_id = f"{bank_type}_{account_type}"
                parser_labels = {
                    "industrial_checking": "BI Checking GTQ",
                    "industrial_usd_checking": "BI Checking USD", 
                    "industrial_credit": "BI Credit GTQ",
                    "industrial_credit_usd": "BI Credit USD",
                    "gyt_credit": "GyT Credit",
                    "bam_credit": "BAM Credit"
                }
                
                results[uploaded_file.filename] = {
                    'suggested': {
                        'bank': bank_type,
                        'account': account_type,
                        'label': parser_labels.get(parser_id, f"{bank_type.title()} {account_type.replace('_', ' ').title()}")
                    },
                    'confidence': 0.8,  # High confidence for keyword-based detection
                    'error': None
                }
            else:
                results[uploaded_file.filename] = {
                    'suggested': None,
                    'confidence': 0,
                    'error': 'Could not detect bank or account type from PDF content'
                }
                
        except Exception as e:
            results[uploaded_file.filename] = {
                'suggested': None,
                'confidence': 0,
                'error': str(e)
            }
    
    return Response({'results': results})


@api_view(['GET'])
def get_parser_types(request):
    """Get available parser types"""
    parser_types = [
        {"id": "industrial_checking", "label": "BI Checking GTQ", "bank": "industrial", "account": "checking"},
        {"id": "industrial_usd_checking", "label": "BI Checking USD", "bank": "industrial", "account": "usd_checking"},
        {"id": "industrial_credit", "label": "BI Credit GTQ", "bank": "industrial", "account": "credit"},
        {"id": "industrial_credit_usd", "label": "BI Credit USD", "bank": "industrial", "account": "credit_usd"},
        {"id": "gyt_credit", "label": "GyT Credit", "bank": "gyt", "account": "credit"},
        {"id": "bam_credit", "label": "BAM Credit", "bank": "bam", "account": "credit"}
    ]
    return Response(parser_types)


@api_view(['GET'])
def get_categories(request):
    """Get all categories with their patterns"""
    categories = []
    for category in Category.objects.filter(parent=None).prefetch_related('subcategories', 'patterns'):
        cat_data = {
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'pattern_count': category.patterns.filter(is_active=True).count(),
            'transaction_count': category.transaction_set.count(),
            'subcategories': []
        }
        
        for subcategory in category.subcategories.all():
            subcat_data = {
                'id': subcategory.id,
                'name': subcategory.name,
                'color': subcategory.color,
                'pattern_count': subcategory.patterns.filter(is_active=True).count(),
                'transaction_count': subcategory.transaction_set.count(),
            }
            cat_data['subcategories'].append(subcat_data)
        
        categories.append(cat_data)
    
    return Response({'categories': categories})


@api_view(['GET'])
def get_transactions(request):
    """Get transactions with optional filtering"""
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    category_id = request.GET.get('category')
    uncategorized_only = request.GET.get('uncategorized', '').lower() == 'true'
    
    transactions = Transaction.objects.select_related('category', 'uploaded_file', 'session')
    
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if uncategorized_only:
        transactions = transactions.filter(category__isnull=True)
    
    transactions = transactions[offset:offset + limit]
    
    transaction_data = []
    for transaction in transactions:
        data = {
            'id': transaction.id,
            'date': transaction.date,
            'description': transaction.description,
            'amount': float(transaction.amount),
            'transaction_type': transaction.transaction_type,
            'account_name': transaction.account_name,
            'account_holder': transaction.account_holder,
            'category': {
                'id': transaction.category.id,
                'name': str(transaction.category),
                'color': transaction.category.color
            } if transaction.category else None,
            'category_confidence': transaction.category_confidence,
            'manually_categorized': transaction.manually_categorized,
        }
        transaction_data.append(data)
    
    return Response({
        'transactions': transaction_data,
        'count': len(transaction_data),
        'has_more': len(transaction_data) == limit
    })


@api_view(['POST'])
def categorize_transaction(request, transaction_id):
    """Manually categorize a transaction"""
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        category_id = request.data.get('category_id')
        
        if category_id:
            category = Category.objects.get(id=category_id)
            transaction.category = category
            transaction.manually_categorized = True
            transaction.category_confidence = 1.0
            transaction.save()
            
            return Response({'message': 'Transaction categorized successfully'})
        else:
            # Remove category
            transaction.category = None
            transaction.manually_categorized = False
            transaction.category_confidence = 0.0
            transaction.save()
            
            return Response({'message': 'Transaction category removed'})
            
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)