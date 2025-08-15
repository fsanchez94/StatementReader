from .base_parser import BaseParser
import pdfplumber
from datetime import datetime
import re

class BancoIndustrialCheckingParser(BaseParser):
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
                # Try to match transaction pattern - handle both formats
                # Format 1: Date DocNo Description Amount Balance (single amount = debit)
                # Format 2: Date DocNo Description  Amount Balance (with space before amount = credit)
                
                # First try: Standard format with amounts before balance
                match = re.match(
                    r'(\d{2}/\d{2}/\d{4})\s+'           # Date
                    r'(\d+)\s+'                         # Document number
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
                        current_balance = float(balance_str.replace(',', ''))
                        
                        amount_value = float(amount_str.replace(',', ''))
                        
                        # Determine transaction type based on balance change and transaction patterns
                        if previous_balance is not None:
                            balance_change = current_balance - previous_balance
                            print(f"  Balance change: {balance_change}")
                            
                            # If balance increased, it's a credit (positive amount)
                            if balance_change > 0:
                                transaction_type = 'credit'
                                amount = abs(amount_value)  # Ensure amount is positive
                            # If balance decreased, it's a debit (negative amount)
                            else:
                                transaction_type = 'debit'
                                amount = -abs(amount_value)  # Ensure amount is negative
                        else:
                            # For first transaction, we cannot reliably determine type without previous balance
                            # Default to treating the amount as shown (positive = credit, negative would be debit)
                            # This will be corrected by subsequent balance changes
                            transaction_type = 'credit'
                            amount = abs(amount_value)
                        
                        previous_balance = current_balance
                        
                        print(f"  Final Amount: {amount}")
                        
                        # Set account name based on spouse status
                        account_name = "Industrial GTQ (Spouse)" if self.is_spouse else "Industrial GTQ"
                        
                        transaction = {
                            'Date': date,
                            'Description': description.strip(),
                            'Original Description': description.strip(),
                            'Amount': amount,
                            'Transaction Type': transaction_type,
                            'Category': '',
                            'Account Name': account_name,
                            'Original Value': abs(amount),
                            'Original Currency': 'GTQ'
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