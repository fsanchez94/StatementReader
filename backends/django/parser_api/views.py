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
                account_holder=uploaded_file.account_holder,
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


def detect_parser_type(text_content):
    """
    Auto-detect bank and account type from PDF text content
    Returns: (bank_type, account_type)
    """
    text_lower = text_content.lower()
    
    # Banco Industrial detection
    if 'banco industrial' in text_lower or 'industrial' in text_lower:
        if 'tarjeta de credito' in text_lower or 'credit card' in text_lower:
            # Check for USD
            if '$' in text_content or 'usd' in text_lower or 'dolar' in text_lower:
                return ('industrial', 'credit_usd')
            return ('industrial', 'credit')
        elif 'cuenta corriente' in text_lower or 'checking' in text_lower:
            # Check for USD
            if '$' in text_content or 'usd' in text_lower or 'dolar' in text_lower:
                return ('industrial', 'usd_checking')
            return ('industrial', 'checking')
    
    # BAM detection
    elif 'bam' in text_lower or 'banco agromercantil' in text_lower:
        if 'tarjeta' in text_lower or 'credit' in text_lower:
            return ('bam', 'credit')
    
    # GyT detection  
    elif 'gyt' in text_lower or 'g&t' in text_lower or 'gyp' in text_lower:
        if 'tarjeta' in text_lower or 'credit' in text_lower:
            return ('gyt', 'credit')
    
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
    
    # Get parser selections and account holders from request
    parsers_data = request.POST.get('parsers', '{}')
    account_holders_data = request.POST.get('account_holders', '{}')
    
    try:
        import json
        parsers = json.loads(parsers_data) if parsers_data else {}
        account_holders = json.loads(account_holders_data) if account_holders_data else {}
    except json.JSONDecodeError:
        parsers = {}
        account_holders = {}
    
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
        
        # Get parser info for this file
        parser_info = parsers.get(file.name, {})
        account_holder = account_holders.get(file.name, 'husband')
        
        uploaded_file = UploadedFile.objects.create(
            session=session,
            filename=file.name,
            file_path=str(file_path),
            bank_type=parser_info.get('bank', ''),
            account_type=parser_info.get('account', ''),
            account_holder=account_holder
        )
        uploaded_files.append(uploaded_file)
    
    session.status = 'ready'
    session.save()
    
    serializer = ProcessingSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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
            
            text_content = pdf_processor.process(uploaded_file.file_path)
            if not text_content.strip():
                uploaded_file.status = 'error'
                uploaded_file.error_message = 'No text content extracted from PDF'
                uploaded_file.save()
                continue
            
            # Get parser info from uploaded file record
            if not uploaded_file.bank_type or not uploaded_file.account_type:
                uploaded_file.status = 'error'
                uploaded_file.error_message = 'No parser type specified for this file'
                uploaded_file.save()
                continue
                
            parser = ParserFactory.get_parser(
                bank_type=uploaded_file.bank_type,
                account_type=uploaded_file.account_type,
                pdf_path=uploaded_file.file_path,
                is_spouse=(uploaded_file.account_holder == 'spouse')
            )
            
            transactions = parser.extract_data()
            if transactions:
                # Save transactions to database
                saved_transactions = save_transactions_to_db(transactions, session, uploaded_file)
                all_transactions.extend(transactions)  # Keep for CSV export
                
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
    
    if all_transactions:
        output_filename = f"all_transactions_{session_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        output_path = settings.TEMP_OUTPUT_DIR / output_filename
        
        import pandas as pd
        df = pd.DataFrame(all_transactions)
        df.to_csv(output_path, index=False)
        
        session.output_file = output_filename
        session.status = 'completed'
    else:
        session.status = 'error'
    
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