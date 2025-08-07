from .base_parser import BaseParser
import pdfplumber
from datetime import datetime
import re

class BancoIndustrialParser(BaseParser):
    def extract_data(self):
        transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                transactions.extend(self._parse_page_text(text))
                
        return transactions
    
    def _parse_page_text(self, text):
        transactions = []
        lines = text.split('\n')
        
        # Skip header lines until we find the column headers
        start_processing = False
        for line in lines:
            if 'Día' in line and 'Docto.' in line and 'Descripción' in line:
                start_processing = True
                continue
                
            if not start_processing or '***SALDO ANTERIOR***' in line:
                continue
                
            # Stop at totals
            if 'TOTALES:' in line:
                break
                
            try:
                # Split the line into components
                match = re.match(r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d,.]+)?\s*([\d,.]+)?\s+([\d,.]+)', line)
                
                if match:
                    date_str, doc_num, description, debit, credit, balance = match.groups()
                    
                    # Convert string values to appropriate types
                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    debit = float(debit.replace(',', '')) if debit else 0.0
                    credit = float(credit.replace(',', '')) if credit else 0.0
                    
                    # Determine amount and transaction type
                    amount = -debit if debit else credit  # negative for debits, positive for credits
                    transaction_type = 'debit' if debit else 'credit'
                    
                    transaction = {
                        'Date': date,
                        'Description': description.strip(),
                        'Original Description': description.strip(),
                        'Amount': amount,
                        'Transaction Type': transaction_type,
                        'Category': '',  # You might want to add logic to categorize transactions
                        'Account Name': 'Banco Industrial'  # You might want to make this configurable
                    }
                    
                    transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing line: {line}")
                print(f"Error: {str(e)}")
                
        return transactions