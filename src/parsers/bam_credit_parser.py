from .base_parser import BaseParser
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
import re
import pdfplumber

class BAMCreditParser(BaseParser):
    def extract_data(self):
        transactions = []
        
        print(f"\n{'='*80}")
        print(f"Processing PDF with OCR")
        print(f"{'='*80}")
        
        try:
            # Convert PDF pages to images
            pages = convert_from_path(self.pdf_path)
            
            for page_num, page in enumerate(pages, 1):
                print(f"\n{'-'*80}")
                print(f"Processing page {page_num} of {len(pages)}")
                print(f"{'-'*80}")
                
                # Extract text from image using OCR
                text = pytesseract.image_to_string(page, lang='spa')
                print("\nRaw OCR text:")
                print(f"{'-'*40}")
                print(text)
                print(f"{'-'*40}\n")
                
                # Process the extracted text
                page_transactions = self._parse_page_text(text.split('\n'))
                transactions.extend(page_transactions)
                print(f"\nFound {len(page_transactions)} transactions on page {page_num}")
                
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            raise
            
        print(f"\n{'='*80}")
        print(f"Total transactions found: {len(transactions)}")
        print(f"{'='*80}")
        return transactions

    def _parse_page_text(self, lines):
        transactions = []
        
        # Keywords to skip (case insensitive)
        skip_keywords = [
            'subtotal',
            '****subtotal',
            'total',
            'saldo anterior',
            'saldo actual',
            'disponible'
        ]
        
        for line in lines:
            print(f"\nProcessing line: {line}")
            
            # Skip lines containing summary keywords
            if any(keyword.lower() in line.lower() for keyword in skip_keywords):
                print(f"Skipping summary line: {line}")
                continue
            
            try:
                # Match pattern with both debit and credit amounts
                match = re.match(
                    r'(\d{2}/\d{2}/\d{4})\s+'  # Fecha consumo
                    r'(\d{2}/\d{2}/\d{4})\s*'  # Fecha cobro
                    r'\|?\s*'  # Optional | separator
                    r'(.+?)\s+'  # Description
                    r'(?:([Q$])\.)([\d,]+\.\d{2})'  # Debit amount with currency capture
                    r'(?:\s+(?:[Q$]\.)([\d,]+\.\d{2}))?'  # Optional credit amount
                    r'\s*$',  # End of line
                    line.strip()
                )
                
                if match:
                    cons_date_str, charge_date_str, description, currency_symbol, debit_str, credit_str = match.groups()
                    credit_str = credit_str or "0.00"  # Default to "0.00" if credit amount is missing
                    
                    # Skip subtotal lines
                    if '****SUBTOTAL' in description:
                        print("Skipping subtotal line")
                        continue
                    
                    print("Parsed values:")
                    print(f"  Transaction Date: {cons_date_str}")
                    print(f"  Charge Date: {charge_date_str}")
                    print(f"  Description: {description.strip()}")
                    print(f"  Currency: {currency_symbol}")
                    print(f"  Debit Amount: {debit_str}")
                    print(f"  Credit Amount: {credit_str}")
                    
                    try:
                        # Convert transaction date (Fecha consumo)
                        date = datetime.strptime(cons_date_str, '%d/%m/%Y').date()
                    except ValueError as e:
                        print(f"Error parsing date {cons_date_str}: {e}")
                        continue
                    
                    description = description.strip()
                    
                    # Determine currency based on the symbol
                    original_currency = 'USD' if currency_symbol == '$' else 'GTQ'
                    
                    # If credit amount is non-zero, it's a credit transaction
                    if credit_str != "0.00":
                        try:
                            original_value = float(credit_str.replace(',', ''))
                            amount = original_value * 7.8 if original_currency == 'USD' else original_value
                            amount = abs(amount)  # Ensure amount is positive
                            transaction_type = 'credit'
                            print(f"Found credit transaction: {amount} GTQ (original: {original_value} {original_currency})")
                        except ValueError:
                            print(f"Error parsing credit amount: {credit_str}")
                            continue
                    # If debit amount is non-zero, it's a debit transaction
                    elif debit_str != "0.00":
                        try:
                            original_value = float(debit_str.replace(',', ''))
                            amount = original_value * 7.8 if original_currency == 'USD' else original_value
                            amount = abs(amount)  # Ensure amount is positive
                            transaction_type = 'debit'
                            print(f"Found debit transaction: {amount} GTQ (original: {original_value} {original_currency})")
                        except ValueError:
                            print(f"Error parsing debit amount: {debit_str}")
                            continue
                    else:
                        print("Skipping: Both amounts are zero")
                        continue
                    
                    transaction = {
                        'Date': date,
                        'Description': description,
                        'Original Description': description,
                        'Amount': amount,
                        'Transaction Type': transaction_type,
                        'Category': '',
                        'Account Name': 'BAM Credit Card',
                        'Original Value': original_value,
                        'Original Currency': original_currency
                    }
                    
                    print(f"Adding transaction: {transaction}")
                    transactions.append(transaction)
                else:
                    print(f"Line did not match expected format: {line}")
                    
            except Exception as e:
                print(f"Error parsing line: {str(e)}")
                
        return transactions

    def _standardize_date(self, date_str):
        """Standardize various date formats to DD/MM/YYYY"""
        # Remove any leading/trailing whitespace
        date_str = date_str.strip()
        
        # Replace various separators with /
        date_str = re.sub(r'[-.]', '/', date_str)
        
        # Split into components
        parts = date_str.split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid date format: {date_str}")
            
        # Pad day and month with leading zeros if needed
        day = parts[0].zfill(2)
        month = parts[1].zfill(2)
        
        # Handle two-digit years
        year = parts[2]
        if len(year) == 2:
            year = '20' + year
            
        return f"{day}/{month}/{year}" 