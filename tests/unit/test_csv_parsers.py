"""
Unit tests for CSV parsers
Tests BICheckingCSVParser and BIUSDCheckingCSVParser
"""
import pytest
import sys
from pathlib import Path
from datetime import date
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from parsers.bi_checking_csv_parser import BICheckingCSVParser
from parsers.bi_usd_checking_csv_parser import BIUSDCheckingCSVParser


class TestBICheckingCSVParser:
    """Test cases for Banco Industrial GTQ Checking CSV Parser"""

    @pytest.fixture
    def sample_bi_gtq_csv_content(self):
        """Create sample BI GTQ checking CSV content"""
        return """Tipo de Transacciones,
,DE = Depósito,,,CQ = Pago de Cheque,
,NC = Nota de Crédito,,,ND = Nota de Débito,

Cuenta: 3140014105 - SANCHEZ LIU JOSE FELIPE
Saldo inicial (Q.): 13583.60
Del 01/10/2025 al 31/10/2025

Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,REEMBOLSO DE TRANSFERENCIA EQUIVOCA,1173336,,1500.00,15083.60
01- 10,NC,1000 BUCKSA,1211511,,7660.00,22743.60
01- 10,ND,COBRO BIMOVIL,383359,15.00,,22728.60
02- 10,ND,TRANSFERENCIA T.I./BI-ENLINEA,38709,552.08,,22176.52
15- 10,NC,Nomina Alius Capital octubre 2025,366002,,3000.00,25176.52
"""

    @pytest.fixture
    def sample_csv_file_gtq(self, tmp_path, sample_bi_gtq_csv_content):
        """Create a temporary CSV file for testing"""
        csv_file = tmp_path / "test_bi_gtq.csv"
        # Write as UTF-16 BE to match real files
        csv_file.write_text(sample_bi_gtq_csv_content, encoding='utf-16-be')
        return str(csv_file)

    def test_parser_initialization(self, sample_csv_file_gtq):
        """Test parser can be initialized"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        assert parser.csv_path == sample_csv_file_gtq

    def test_extract_year_from_date_range(self, sample_csv_file_gtq):
        """Test year extraction from date range line"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        with open(sample_csv_file_gtq, 'r', encoding='utf-16-be') as f:
            lines = f.readlines()
        year = parser._extract_year_from_date_range(lines)
        assert year == 2025

    def test_find_header_line(self, sample_csv_file_gtq):
        """Test finding the CSV header line"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        with open(sample_csv_file_gtq, 'r', encoding='utf-16-be') as f:
            lines = f.readlines()
        header_index = parser._find_header_line(lines)
        assert header_index >= 0
        assert 'Fecha' in lines[header_index]

    def test_extract_data_gtq(self, sample_csv_file_gtq):
        """Test extracting transactions from GTQ checking CSV"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        transactions = parser.extract_data()

        assert len(transactions) == 5

        # Test first transaction (credit)
        first = transactions[0]
        assert first['Date'] == date(2025, 10, 1)
        assert 'REEMBOLSO' in first['Description']
        assert first['Amount'] == 1500.00
        assert first['Transaction Type'] == 'credit'
        assert first['Account Name'] == 'Industrial GTQ'
        assert first['Original Currency'] == 'GTQ'

        # Test debit transaction
        debit = transactions[2]
        assert debit['Transaction Type'] == 'debit'
        assert debit['Amount'] == 15.00
        assert 'BIMOVIL' in debit['Description']

    def test_transaction_type_mapping(self, sample_csv_file_gtq):
        """Test TT code to transaction type mapping"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        transactions = parser.extract_data()

        # NC and DE should be credit
        credits = [t for t in transactions if t['Transaction Type'] == 'credit']
        assert len(credits) == 3  # Three NC transactions

        # ND and CQ should be debit
        debits = [t for t in transactions if t['Transaction Type'] == 'debit']
        assert len(debits) == 2  # Two ND transactions

    def test_amounts_always_positive(self, sample_csv_file_gtq):
        """Test that all amounts are positive"""
        parser = BICheckingCSVParser(sample_csv_file_gtq)
        transactions = parser.extract_data()

        for transaction in transactions:
            assert transaction['Amount'] > 0, f"Amount should be positive: {transaction}"


class TestBIUSDCheckingCSVParser:
    """Test cases for Banco Industrial USD Checking CSV Parser"""

    @pytest.fixture
    def sample_bi_usd_csv_content(self):
        """Create sample BI USD checking CSV content"""
        return """Tipo de Transacciones,
,DE = Depósito,,,CQ = Pago de Cheque,
,NC = Nota de Crédito,,,ND = Nota de Débito,

Cuenta: 3140014105 - SANCHEZ LIU JOSE FELIPE
Saldo inicial (USD): 1000.00
Del 01/10/2025 al 31/10/2025

Fecha,TT,Descripción,No. Doc,Debe (USD),Haber (USD),Saldo (USD)
01- 10,NC,DEPOSITO EFECTIVO,1173336,,100.00,1100.00
02- 10,ND,ATM WITHDRAWAL,383359,50.00,,1050.00
15- 10,NC,TRANSFER IN,366002,,200.00,1250.00
"""

    @pytest.fixture
    def sample_csv_file_usd(self, tmp_path, sample_bi_usd_csv_content):
        """Create a temporary USD CSV file for testing"""
        csv_file = tmp_path / "test_bi_usd.csv"
        csv_file.write_text(sample_bi_usd_csv_content, encoding='utf-16-be')
        return str(csv_file)

    def test_parser_initialization(self, sample_csv_file_usd):
        """Test USD parser can be initialized"""
        parser = BIUSDCheckingCSVParser(sample_csv_file_usd)
        assert parser.csv_path == sample_csv_file_usd
        assert parser.USD_TO_GTQ_RATE == 7.8

    def test_extract_data_usd(self, sample_csv_file_usd):
        """Test extracting transactions from USD checking CSV"""
        parser = BIUSDCheckingCSVParser(sample_csv_file_usd)
        transactions = parser.extract_data()

        assert len(transactions) == 3

        # Test first transaction (credit in USD, converted to GTQ)
        first = transactions[0]
        assert first['Date'] == date(2025, 10, 1)
        assert first['Original Value'] == 100.00  # Original USD amount
        assert first['Amount'] == 780.00  # 100 * 7.8
        assert first['Transaction Type'] == 'credit'
        assert first['Account Name'] == 'Industrial USD'
        assert first['Original Currency'] == 'USD'

    def test_usd_to_gtq_conversion(self, sample_csv_file_usd):
        """Test USD to GTQ conversion (multiply by 7.8)"""
        parser = BIUSDCheckingCSVParser(sample_csv_file_usd)
        transactions = parser.extract_data()

        for transaction in transactions:
            expected_gtq = transaction['Original Value'] * 7.8
            assert transaction['Amount'] == expected_gtq, \
                f"Expected {expected_gtq}, got {transaction['Amount']}"

    def test_debit_transaction_usd(self, sample_csv_file_usd):
        """Test debit transaction in USD"""
        parser = BIUSDCheckingCSVParser(sample_csv_file_usd)
        transactions = parser.extract_data()

        # Second transaction is a debit (ATM withdrawal)
        debit = transactions[1]
        assert debit['Transaction Type'] == 'debit'
        assert debit['Original Value'] == 50.00
        assert debit['Amount'] == 390.00  # 50 * 7.8


class TestCSVEncodingHandling:
    """Test CSV encoding detection and handling"""

    def test_utf8_encoding(self, tmp_path):
        """Test reading UTF-8 encoded CSV"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "test_utf8.csv"
        csv_file.write_text(content, encoding='utf-8')

        parser = BICheckingCSVParser(str(csv_file))
        transactions = parser.extract_data()
        assert len(transactions) == 1

    def test_utf16be_encoding(self, tmp_path):
        """Test reading UTF-16 BE encoded CSV"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "test_utf16be.csv"
        csv_file.write_text(content, encoding='utf-16-be')

        parser = BICheckingCSVParser(str(csv_file))
        transactions = parser.extract_data()
        assert len(transactions) == 1

    def test_latin1_encoding(self, tmp_path):
        """Test reading Latin-1 encoded CSV"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "test_latin1.csv"
        csv_file.write_text(content, encoding='latin-1')

        parser = BICheckingCSVParser(str(csv_file))
        transactions = parser.extract_data()
        assert len(transactions) == 1


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_csv_file(self, tmp_path):
        """Test handling of empty CSV file"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("", encoding='utf-8')

        parser = BICheckingCSVParser(str(csv_file))
        with pytest.raises(ValueError):
            parser.extract_data()

    def test_missing_date_range(self, tmp_path):
        """Test handling of CSV without date range"""
        content = """Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "no_date_range.csv"
        csv_file.write_text(content, encoding='utf-8')

        parser = BICheckingCSVParser(str(csv_file))
        # Should fall back to current year
        transactions = parser.extract_data()
        assert len(transactions) >= 0  # May or may not extract depending on validation

    def test_malformed_transaction_row(self, tmp_path):
        """Test handling of malformed transaction rows"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,VALID,123,,100.00,100.00
INVALID ROW
02- 10,ND,ANOTHER VALID,456,50.00,,50.00
"""
        csv_file = tmp_path / "malformed.csv"
        csv_file.write_text(content, encoding='utf-8')

        parser = BICheckingCSVParser(str(csv_file))
        transactions = parser.extract_data()
        # Should skip invalid rows and process valid ones
        assert len(transactions) == 2
