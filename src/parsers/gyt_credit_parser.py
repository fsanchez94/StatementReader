from .base_parser import BaseParser
import pdfplumber
from datetime import datetime
import re

class GyTCreditParser(BaseParser):
    def extract_data(self):
        transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"\nProcessing PDF with {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\nProcessing page {page_num} of {len(pdf.pages)}")
                text = page.extract_text()
                
                # Process all lines
                page_transactions = self._parse_page_text(text.split('\n'))
                transactions.extend(page_transactions)
                print(f"Found {len(page_transactions)} transactions on page {page_num}")
                
        print(f"\nTotal transactions found: {len(transactions)}")
        return transactions

    def _parse_page_text(self, lines):
        transactions = []
        
        # Keywords to skip (case insensitive)
        skip_keywords = [
            'subtotal',
            'total',
            'saldo anterior',
            'saldo actual',
            'disponible',
            'fecha',  # Skip header
            'referencia',  # Skip header
            'descripción',  # Skip header
            'crédito/débito'  # Skip header
        ]
        
        for line in lines:
            print(f"\nProcessing line: {line}")
            
            # Skip lines containing summary keywords
            if any(keyword.lower() in line.lower() for keyword in skip_keywords):
                print(f"Skipping summary line: {line}")
                continue
            
            try:
                # Match pattern for transactions
                match = re.match(
                    r'(\d{2}/\d{2}/\d{4})\s+'          # Fecha
                    r'([A-Z0-9]+)\s+'                   # Referencia (alphanumeric)
                    r'(.+?)\s+'                         # Descripción (non-greedy match)
                    r'(-?(?:QTZ|GTQ|DOL|USD))\s+'      # Currency with optional minus sign (all variations)
                    r'([\d,]+\.?\d{2})'                # Amount
                    r'\s*$',                            # End of line
                    line.strip()
                )
                
                if match:
                    date_str, reference, description, currency_code, amount_str = match.groups()
                    
                    print("Parsed values:")
                    print(f"  Date: {date_str}")
                    print(f"  Reference: {reference}")
                    print(f"  Description: {description.strip()}")
                    print(f"  Currency: {currency_code}")
                    print(f"  Amount: {amount_str}")
                    
                    try:
                        date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except ValueError as e:
                        print(f"Error parsing date {date_str}: {e}")
                        continue
                    
                    description = description.strip()
                    # Remove the minus sign from currency code for determining currency type
                    clean_currency = currency_code.replace('-', '')
                    original_currency = 'USD' if clean_currency in ['DOL', 'USD'] else 'GTQ'
                    
                    try:
                        # Parse amount
                        original_value = float(amount_str.replace(',', ''))
                        # Make amount negative if currency has minus sign
                        if currency_code.startswith('-'):
                            original_value = -original_value
                            
                        # Convert USD to GTQ if necessary
                        amount = original_value * 7.8 if original_currency == 'USD' else original_value
                        
                        # Determine transaction type based on amount sign
                        transaction_type = 'credit' if amount >= 0 else 'debit'
                        
                        print(f"Found {transaction_type} transaction: {amount} GTQ (original: {original_value} {original_currency})")
                    except ValueError:
                        print(f"Error parsing amount: {amount_str}")
                        continue
                    
                    # Set account name based on spouse status
                    account_name = "GyT 5978 (Spouse)" if self.is_spouse else "GyT 5978"
                    
                    transaction = {
                        'Date': date,
                        'Description': description,
                        'Original Description': description,
                        'Amount': amount,
                        'Transaction Type': transaction_type,
                        'Category': '',
                        'Account Name': account_name,
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