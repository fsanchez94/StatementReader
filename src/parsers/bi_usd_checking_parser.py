from .base_parser import BaseParser
import pdfplumber
from datetime import datetime
import re

class BIUSDCheckingParser(BaseParser):
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
        previous_balance = None
        
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
            'débito',  # Skip header
            'crédito',  # Skip header
            'saldo'  # Skip header
        ]
        
        for line in lines:
            print(f"\nProcessing line: {line}")
            
            # Skip lines containing summary keywords
            if any(keyword.lower() in line.lower() for keyword in skip_keywords):
                print(f"Skipping summary line: {line}")
                continue
            
            try:
                # Match pattern for transactions - handle real PDF format
                match = re.match(
                    r'(\d{2}/\d{2}/\d{4})\s+'           # Date
                    r'(\d+)\s+'                         # Document number (required)
                    r'(.+?)\s+'                         # Description (non-greedy)
                    r'([\d,]+\.\d{2})\s+'               # Amount 
                    r'([\d,]+\.\d{2})'                  # Balance
                    r'\s*$',                            # End of line
                    line.strip()
                )
                
                if match:
                    date_str, reference, description, amount_str, balance_str = match.groups()
                    
                    print("Parsed values:")
                    print(f"  Date: {date_str}")
                    print(f"  Reference: {reference or 'N/A'}")
                    print(f"  Description: {description.strip()}")
                    print(f"  Amount: {amount_str}")
                    print(f"  Balance: {balance_str}")
                    print(f"  Previous Balance: {previous_balance}")
                    
                    try:
                        date = datetime.strptime(date_str, '%d/%m/%Y').date()
                        amount_usd = float(amount_str.replace(',', ''))
                        current_balance_usd = float(balance_str.replace(',', ''))
                        # Convert USD to GTQ for internal calculations
                        amount_gtq = amount_usd * 7.8
                        current_balance_gtq = current_balance_usd * 7.8
                        
                        # Determine transaction type based on balance change and transaction patterns
                        # All amounts are always positive in the output
                        amount = abs(amount_gtq)

                        if previous_balance is not None:
                            balance_change = current_balance_gtq - previous_balance
                            print(f"  Balance change: {balance_change}")

                            # If balance increased, it's a credit
                            if balance_change > 0:
                                transaction_type = 'credit'
                            # If balance decreased, it's a debit
                            else:
                                transaction_type = 'debit'
                        else:
                            # For first transaction, we cannot reliably determine type without previous balance
                            # Default to credit
                            transaction_type = 'credit'
                        
                        previous_balance = current_balance_gtq
                        
                        print(f"  Transaction Type: {transaction_type}")
                        print(f"  Final Amount: {amount}")
                        
                        # Set account name
                        account_name = "Industrial USD 9384"
                        
                        transaction = {
                            'Date': date,
                            'Description': description.strip(),
                            'Original Description': description.strip(),
                            'Amount': amount,
                            'Transaction Type': transaction_type,
                            'Category': '',
                            'Account Name': account_name,
                            'Original Value': abs(amount_usd),
                            'Original Currency': 'USD'
                        }
                        
                        print(f"Adding transaction: {transaction}")
                        transactions.append(transaction)
                        
                    except ValueError as e:
                        print(f"Error parsing numbers: {str(e)}")
                        continue
                else:
                    print(f"Line did not match expected format: {line}")
                    
            except Exception as e:
                print(f"Error parsing line: {str(e)}")
                
        return transactions 