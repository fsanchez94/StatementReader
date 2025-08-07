from .base_parser import BaseParser
import pdfplumber
from datetime import datetime
import re

class BancoIndustrialCreditUSDParser(BaseParser):
    # Define valid transaction types
    DEBIT_TYPES = {"DEBITO", "CONSUMO"}
    CREDIT_TYPES = {"PAGO AGENC", "PAGO", "CREDITO"}
    
    def extract_data(self):
        transactions = []
        unknown_types = set()  # To track any unknown transaction types
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"\nProcessing PDF with {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\nProcessing page {page_num} of {len(pdf.pages)}")
                text = page.extract_text()
                
                # For pages after the first one, we don't need to wait for headers
                page_transactions, page_unknown_types = self._parse_page_text(text, is_first_page=(page_num == 1))
                transactions.extend(page_transactions)
                unknown_types.update(page_unknown_types)
                print(f"Found {len(page_transactions)} transactions on page {page_num}")
        
        # Report any unknown transaction types found
        if unknown_types:
            error_msg = "\nERROR: Found unknown transaction types:\n"
            for unknown_type in sorted(unknown_types):
                error_msg += f"- {unknown_type}\n"
            error_msg += "\nPlease update the parser to handle these transaction types."
            raise ValueError(error_msg)
                
        print(f"\nTotal transactions found: {len(transactions)}")
        return transactions

    def _parse_page_text(self, text, is_first_page=False):
        transactions = []
        unknown_types = set()
        lines = text.split('\n')
        start_processing = not is_first_page
        
        # Process lines
        for line in lines:
            print(f"\nProcessing line: {line}")
            
            # Look for column headers (with typo in MOVMIENTO) - only needed for first page
            if is_first_page and 'FECHA' in line and 'TIPO DE MOVMIENTO' in line and 'COMERCIO' in line:
                start_processing = True
                print("Found headers, starting processing")
                continue
            
            # Skip until we find headers (only on first page)
            if is_first_page and not start_processing:
                continue
            
            # Skip footer lines
            if any(skip in line for skip in ['FAVOR DE REVISAR', 'MES CALENDARIO', 'Saldo al final']):
                print("Skipping footer line")
                continue
                
            try:
                # Match lines with date, transaction type, doc number, establishment, amount (with $.), and balance
                match = re.match(r'(\d{2}/\d{2}/\d{4})\s+([A-Z\s]+)\s+(\d+)\s+(.+?)\s+\$\.\s*([\d,]+\.\d{2})\s+\$\.\s*([\d,]+\.\d{2})', line)
                
                if match:
                    date_str, trans_type, doc_num, establishment, amount_str, balance_str = match.groups()
                    
                    # Convert strings to numbers
                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    amount = float(amount_str.replace(',', ''))
                    
                    # Convert USD to GTQ
                    amount_gtq = amount * 7.8
                    
                    # Clean up strings
                    trans_type = trans_type.strip()
                    establishment = establishment.strip()
                    
                    print(f"Date: {date}")
                    print(f"Transaction Type: {trans_type}")
                    print(f"Establishment: {establishment}")
                    print(f"Amount (USD): {amount}")
                    print(f"Amount (GTQ): {amount_gtq}")
                    
                    # Determine if amount should be negative or positive
                    if trans_type in self.DEBIT_TYPES:
                        amount_gtq = -amount_gtq
                        transaction_type = 'debit'
                    elif trans_type in self.CREDIT_TYPES:
                        transaction_type = 'credit'
                    else:
                        # Track unknown transaction type
                        unknown_types.add(trans_type)
                        print(f"Found unknown transaction type: {trans_type}")
                        continue
                    
                    # Set account name based on spouse status
                    account_name = "BI 1116 USD (Spouse)" if self.is_spouse else "BI 1116 USD"
                    
                    transaction = {
                        'Date': date,
                        'Description': establishment,
                        'Original Description': establishment,
                        'Amount': amount_gtq,
                        'Transaction Type': transaction_type,
                        'Category': '',
                        'Account Name': account_name,
                        'Original Value': abs(amount),
                        'Original Currency': 'USD'
                    }
                    
                    print(f"Adding transaction: {transaction}")
                    transactions.append(transaction)
                    
            except Exception as e:
                print(f"Error parsing line: {line}")
                print(f"Error: {str(e)}")
                
        return transactions, unknown_types 