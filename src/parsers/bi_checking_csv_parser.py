from .base_parser import BaseParser
import pandas as pd
import re
from datetime import datetime

class BICheckingCSVParser(BaseParser):
    """Parser for Banco Industrial GTQ Checking Account CSV statements"""

    def __init__(self, csv_path, is_spouse=False):
        # Call parent constructor but rename parameter for CSV
        super().__init__(csv_path, is_spouse)
        self.csv_path = csv_path

    def extract_data(self):
        """Extract transaction data from BI checking CSV file"""
        transactions = []

        try:
            # Try multiple encodings to read the CSV file
            encodings = ['utf-8', 'utf-16-be', 'utf-16-le', 'latin-1', 'cp1252']
            lines = None
            working_encoding = None

            for encoding in encodings:
                try:
                    with open(self.csv_path, 'r', encoding=encoding) as f:
                        test_lines = f.readlines()
                        # Check if this encoding produces readable content
                        if any('Fecha' in line or 'fecha' in line.lower() for line in test_lines[:15]):
                            # Verify pandas can also read with this encoding
                            try:
                                test_df = pd.read_csv(self.csv_path, encoding=encoding, nrows=1)
                                lines = test_lines
                                working_encoding = encoding
                                print(f"Successfully reading CSV with encoding: {encoding}")
                                break
                            except:
                                # Pandas can't parse with this encoding, try next
                                continue
                except:
                    continue

            if not lines or not working_encoding:
                raise ValueError("Could not read CSV file with any known encoding")

            # Extract year from date range line (line 7: "Del 01/10/2025 al 31/10/2025")
            year = self._extract_year_from_date_range(lines)

            # Find the header line (should be line 9, but we'll search for it)
            header_line_index = self._find_header_line(lines)

            if header_line_index == -1:
                raise ValueError("Could not find CSV header line with 'Fecha,TT,Descripción'")

            # Read CSV data starting from header line using the working encoding
            df = pd.read_csv(
                self.csv_path,
                encoding=working_encoding,
                skiprows=header_line_index,
                on_bad_lines='skip'
            )

            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()

            # Validate required columns
            self._validate_columns(df)

            # Process each transaction
            for idx, row in df.iterrows():
                try:
                    transaction = self._parse_transaction_row(row, year)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    print(f"Warning: Skipping row {idx}: {str(e)}")
                    continue

            print(f"\nTotal transactions found: {len(transactions)}")
            return transactions

        except Exception as e:
            print(f"Error processing CSV: {str(e)}")
            raise

    def _extract_year_from_date_range(self, lines):
        """Extract year from the date range line"""
        # Look for line like: "Del 01/10/2025 al 31/10/2025"
        for line in lines[:10]:  # Check first 10 lines
            match = re.search(r'Del\s+\d{2}/\d{2}/(\d{4})', line)
            if match:
                year = int(match.group(1))
                print(f"Extracted year: {year}")
                return year

        # Fallback to current year if not found
        current_year = datetime.now().year
        print(f"Warning: Could not extract year from CSV, using current year: {current_year}")
        return current_year

    def _find_header_line(self, lines):
        """Find the line number where the CSV header starts"""
        for idx, line in enumerate(lines):
            # Look for header with "Fecha,TT,Descripción"
            if 'Fecha' in line and 'TT' in line and 'Descripci' in line:
                print(f"Found header at line {idx + 1}")
                return idx
        return -1

    def _validate_columns(self, df):
        """Validate that required columns are present"""
        required_columns = ['Fecha', 'TT', 'No. Doc']

        # Check for Descripción with possible encoding variations
        has_description = any('Descripci' in col for col in df.columns)
        if not has_description:
            raise ValueError("Missing 'Descripción' column")

        # Check for Debe/Haber columns (they might have (Q.) suffix)
        has_debe = any('Debe' in col for col in df.columns)
        has_haber = any('Haber' in col for col in df.columns)

        if not has_debe or not has_haber:
            raise ValueError("Missing 'Debe' or 'Haber' columns")

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

    def _parse_transaction_row(self, row, year):
        """Parse a single transaction row from the CSV"""

        # Get fecha (format: "01- 10" or "01-10")
        fecha_str = str(row['Fecha']).strip()

        # Skip if not a valid date format
        if not re.match(r'\d{1,2}\s*-\s*\d{1,2}', fecha_str):
            return None

        # Parse date
        date_parts = fecha_str.replace(' ', '').split('-')
        day = int(date_parts[0])
        month = int(date_parts[1])
        date_obj = datetime(year, month, day).date()

        # Get transaction type code
        tt_code = str(row['TT']).strip().upper()

        # Map TT code to transaction type
        # NC (Nota de Crédito) = credit
        # ND (Nota de Débito) = debit
        # DE (Depósito) = credit
        # CQ (Pago de Cheque) = debit
        if tt_code in ['NC', 'DE']:
            transaction_type = 'credit'
        elif tt_code in ['ND', 'CQ']:
            transaction_type = 'debit'
        else:
            print(f"Warning: Unknown TT code '{tt_code}', defaulting to debit")
            transaction_type = 'debit'

        # Get description (handle encoding issues)
        desc_col = [col for col in row.index if 'Descripci' in col][0]
        description = str(row[desc_col]).strip()

        # Get amount from Debe or Haber column
        debe_col = [col for col in row.index if 'Debe' in col][0]
        haber_col = [col for col in row.index if 'Haber' in col][0]

        debe_value = str(row[debe_col]).strip()
        haber_value = str(row[haber_col]).strip()

        # Parse amount (use Debe if present, otherwise Haber)
        if debe_value and debe_value != '' and debe_value != 'nan':
            amount = float(debe_value.replace(',', ''))
        elif haber_value and haber_value != '' and haber_value != 'nan':
            amount = float(haber_value.replace(',', ''))
        else:
            print(f"Warning: No amount found for transaction on {fecha_str}")
            return None

        # Ensure amount is always positive
        amount = abs(amount)

        # Build transaction dictionary
        transaction = {
            'Date': date_obj,
            'Description': description,
            'Original Description': description,
            'Amount': amount,
            'Transaction Type': transaction_type,
            'Category': '',
            'Account Name': 'Industrial GTQ',
            'Original Value': amount,
            'Original Currency': 'GTQ'
        }

        return transaction
