import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from src.parsers.banco_industrial_checking_parser import BancoIndustrialCheckingParser
from src.parsers.banco_industrial_credit_parser import BancoIndustrialCreditParser
from src.parsers.bam_credit_parser import BAMCreditParser
from src.parsers.gyt_credit_parser import GyTCreditParser

# Add fixtures to path for real PDF testing
sys.path.append(str(Path(__file__).parent.parent / "fixtures"))

try:
    from test_data_loader import (
        get_sample_pdfs_by_type, 
        require_sample_pdfs,
        has_sample_pdfs
    )
    REAL_PDF_TESTING_AVAILABLE = True
except ImportError:
    REAL_PDF_TESTING_AVAILABLE = False

class TestBancoIndustrialCheckingParser:
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = BancoIndustrialCheckingParser("test.pdf")
        self.parser_spouse = BancoIndustrialCheckingParser("test.pdf", is_spouse=True)

    def test_init(self):
        """Test parser initialization"""
        assert self.parser.pdf_path == "test.pdf"
        assert self.parser.is_spouse is False
        assert self.parser_spouse.is_spouse is True

    def test_parse_valid_transaction_line_debit(self):
        """Test parsing a debit transaction identified through balance change"""
        lines = [
            "15/01/2024 123456 DEPOSITO INICIAL  500.00 2,000.00",           # First (defaults to credit)
            "16/01/2024 123457 PAGO TARJETA DE CREDITO 1,500.00  500.00"     # Second (debit by balance change)
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        transaction = transactions[1]  # Test the second transaction
        
        assert transaction['Date'] == date(2024, 1, 16)
        assert transaction['Description'] == 'PAGO TARJETA DE CREDITO'
        assert transaction['Original Description'] == 'PAGO TARJETA DE CREDITO'
        # Balance decreased, so it's a debit (negative amount)
        assert transaction['Amount'] == -1500.00
        assert transaction['Transaction Type'] == 'debit'
        assert transaction['Account Name'] == 'Industrial GTQ'
        assert transaction['Category'] == ''

    def test_parse_valid_transaction_line_credit(self):
        """Test parsing a valid credit transaction line"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction['Date'] == date(2024, 1, 15)
        assert transaction['Description'] == 'DEPOSITO EFECTIVO'
        assert transaction['Original Description'] == 'DEPOSITO EFECTIVO'
        # Amount in Crédito column, so it's a credit (positive amount)
        assert transaction['Amount'] == 500.00
        assert transaction['Transaction Type'] == 'credit'
        assert transaction['Account Name'] == 'Industrial GTQ'
        assert transaction['Category'] == ''

    def test_parse_transaction_line_spouse_account(self):
        """Test parsing transaction for spouse account"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"]
        
        transactions = self.parser_spouse._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Account Name'] == 'Industrial GTQ (Spouse)'

    def test_parse_multiple_transactions(self):
        """Test parsing multiple transaction lines"""
        lines = [
            "15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00",  # Credit
            "16/01/2024 123457 PAGO SERVICIOS 200.00  1,800.00"     # Debit
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        
        # First transaction: amount in Crédito column
        assert transactions[0]['Transaction Type'] == 'credit'
        assert transactions[0]['Amount'] == 500.00
        
        # Second transaction: amount in Débito column  
        assert transactions[1]['Transaction Type'] == 'debit'
        assert transactions[1]['Amount'] == -200.00

    def test_skip_summary_lines(self):
        """Test that summary lines are skipped"""
        lines = [
            "SUBTOTAL DE CREDITOS 1,500.00",
            "TOTAL DE DEBITOS 500.00",
            "SALDO ANTERIOR 1,000.00",
            "15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00",
            "SALDO ACTUAL 2,000.00"
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        # Only the valid transaction line should be parsed
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    def test_skip_header_lines(self):
        """Test that header lines are skipped"""
        lines = [
            "FECHA REFERENCIA DESCRIPCIÓN DÉBITO CRÉDITO SALDO",
            "15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    def test_parse_line_with_reference_number(self):
        """Test parsing line with reference number"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    def test_parse_line_with_comma_in_amounts(self):
        """Test parsing line with comma-separated amounts"""
        lines = ["15/01/2024 123456 DEPOSITO GRANDE  1,500.50 10,000.75"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Amount'] == 1500.50

    def test_invalid_date_format(self):
        """Test handling of invalid date format"""
        lines = ["2024/01/15 123456 DEPOSITO EFECTIVO 500.00 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        # Should skip invalid date format
        assert len(transactions) == 0

    def test_invalid_amount_format(self):
        """Test handling of invalid amount format"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO invalid_amount 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        # Should skip invalid amount
        assert len(transactions) == 0

    def test_malformed_line(self):
        """Test handling of malformed transaction lines"""
        lines = [
            "This is not a transaction line",
            "15/01/2024 incomplete line",
            "15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"  # Valid line
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        # Only the valid line should be parsed
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    @patch('src.parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_extract_data_integration(self, mock_pdfplumber):
        """Test the main extract_data method"""
        # Setup mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = """FECHA REFERENCIA DESCRIPCIÓN DÉBITO CRÉDITO SALDO
15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00
16/01/2024 123457 PAGO SERVICIOS 200.00  1,800.00"""
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Suppress print statements for cleaner test output
        with patch('builtins.print'):
            transactions = self.parser.extract_data()
        
        assert len(transactions) == 2
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'
        assert transactions[1]['Description'] == 'PAGO SERVICIOS'

    @patch('src.parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_extract_data_multiple_pages(self, mock_pdfplumber):
        """Test extract_data with multiple PDF pages"""
        # Setup mock PDF with multiple pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "16/01/2024 123457 PAGO SERVICIOS 200.00  1,800.00"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        with patch('builtins.print'):
            transactions = self.parser.extract_data()
        
        assert len(transactions) == 2

    def test_transaction_with_debit_column(self):
        """Test transaction identified as debit through balance change"""
        lines = [
            "15/01/2024 123456 DEPOSITO INICIAL  500.00 2,000.00",   # First (defaults to credit)
            "16/01/2024 123457 RETIRO CAJERO 1,000.00  1,000.00"    # Second (debit by balance change)
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        transaction = transactions[1]  # Test the second transaction
        
        assert transaction['Description'] == 'RETIRO CAJERO'
        assert transaction['Transaction Type'] == 'debit'
        assert transaction['Amount'] == -1000.00  # Negative for debit
        
    def test_transaction_with_credit_column(self):
        """Test transaction with amount in Crédito column"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO  500.00 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction['Description'] == 'DEPOSITO EFECTIVO'
        assert transaction['Transaction Type'] == 'credit'
        assert transaction['Amount'] == 500.00  # Positive for credit
        
    def test_large_transaction_amounts(self):
        """Test parsing of large transaction amounts"""
        lines = [
            "15/01/2024 123456 DEPOSITO INICIAL  1,000.00 10,000.00",  # First (defaults to credit)
            "16/01/2024 123457 RETIRO GRANDE 9,500.00  500.00"         # Second (debit by balance change)
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        transaction = transactions[1]  # Test the second transaction
        
        assert transaction['Transaction Type'] == 'debit'
        assert transaction['Amount'] == -9500.00
        
    def test_transaction_with_large_credit(self):
        """Test transaction with large credit amount"""
        lines = ["15/01/2024 123456 DEPOSITO INICIAL  1,000.00 1,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction['Transaction Type'] == 'credit'
        assert transaction['Amount'] == 1000.00


class TestParserEdgeCases:
    """Test edge cases that apply to multiple parsers"""
    
    def test_empty_pdf_content(self):
        """Test handling of empty PDF content"""
        parser = BancoIndustrialCheckingParser("test.pdf")
        
        with patch('parsers.banco_industrial_checking_parser.pdfplumber.open') as mock_pdfplumber:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__.return_value = mock_pdf
            mock_pdf.__exit__.return_value = None
            
            mock_pdfplumber.return_value = mock_pdf
            
            with patch('builtins.print'):
                transactions = parser.extract_data()
            
            assert len(transactions) == 0

    def test_pdf_with_no_pages(self):
        """Test handling of PDF with no pages"""
        parser = BancoIndustrialCheckingParser("test.pdf")
        
        with patch('parsers.banco_industrial_checking_parser.pdfplumber.open') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = []
            mock_pdf.__enter__.return_value = mock_pdf
            mock_pdf.__exit__.return_value = None
            
            mock_pdfplumber.return_value = mock_pdf
            
            with patch('builtins.print'):
                transactions = parser.extract_data()
            
            assert len(transactions) == 0

    def test_balance_calculation_edge_cases(self):
        """Test balance change calculation edge cases"""
        parser = BancoIndustrialCheckingParser("test.pdf")
        
        # Test when balances are equal (no change)
        lines = [
            "15/01/2024 123456 FIRST TRANSACTION 500.00 2,000.00",
            "16/01/2024 123457 SECOND TRANSACTION 0.00 2,000.00"
        ]
        
        transactions = parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        # Second transaction should be debit since balance didn't change
        # but there was still a transaction amount
        assert transactions[1]['Transaction Type'] == 'debit'

    def test_very_large_amounts(self):
        """Test parsing of very large monetary amounts"""
        parser = BancoIndustrialCheckingParser("test.pdf")
        
        lines = ["15/01/2024 123456 LARGE DEPOSIT 1,000,000.99 5,000,000.50"]
        
        transactions = parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Amount'] == 1000000.99


@pytest.mark.skipif(not REAL_PDF_TESTING_AVAILABLE, reason="Real PDF testing not available")
class TestParsersWithRealPDFs:
    """Integration tests using real PDF files when available"""
    
    @pytest.mark.skipif(not has_sample_pdfs("industrial", "checking"), 
                       reason="No industrial checking sample PDFs available")
    def test_industrial_checking_with_real_pdf(self):
        """Test Industrial checking parser with real PDF samples"""
        pdf_files = get_sample_pdfs_by_type("industrial", "checking")
        
        for pdf_path in pdf_files[:1]:  # Test first PDF only for unit tests
            parser = BancoIndustrialCheckingParser(pdf_path)
            transactions = parser.extract_data()
            
            # Should return a list
            assert isinstance(transactions, list)
            
            # If transactions found, validate structure
            if transactions:
                transaction = transactions[0]
                assert 'Date' in transaction
                assert 'Description' in transaction
                assert 'Amount' in transaction
                assert 'Transaction Type' in transaction
                assert 'Account Name' in transaction
                assert transaction['Account Name'] == 'Industrial GTQ'
    
    @pytest.mark.skipif(not has_sample_pdfs("industrial", "credit"), 
                       reason="No industrial credit sample PDFs available")
    def test_industrial_credit_with_real_pdf(self):
        """Test Industrial credit parser with real PDF samples"""
        pdf_files = get_sample_pdfs_by_type("industrial", "credit")
        
        for pdf_path in pdf_files[:1]:  # Test first PDF only for unit tests
            parser = BancoIndustrialCreditParser(pdf_path)
            transactions = parser.extract_data()
            
            # Should return a list
            assert isinstance(transactions, list)
            
            # If transactions found, validate structure
            if transactions:
                transaction = transactions[0]
                assert 'Date' in transaction
                assert 'Description' in transaction
                assert 'Amount' in transaction
                assert 'Transaction Type' in transaction
                assert 'Account Name' in transaction
    
    @pytest.mark.skipif(not has_sample_pdfs("bam", "credit"), 
                       reason="No BAM credit sample PDFs available")
    def test_bam_credit_with_real_pdf(self):
        """Test BAM credit parser with real PDF samples"""
        pdf_files = get_sample_pdfs_by_type("bam", "credit")
        
        for pdf_path in pdf_files[:1]:  # Test first PDF only for unit tests
            parser = BAMCreditParser(pdf_path)
            transactions = parser.extract_data()
            
            # Should return a list
            assert isinstance(transactions, list)
            
            # If transactions found, validate structure
            if transactions:
                transaction = transactions[0]
                assert 'Date' in transaction
                assert 'Description' in transaction
                assert 'Amount' in transaction
                assert 'Transaction Type' in transaction
                assert 'Account Name' in transaction
    
    @pytest.mark.skipif(not has_sample_pdfs("gyt", "credit"), 
                       reason="No GyT credit sample PDFs available")
    def test_gyt_credit_with_real_pdf(self):
        """Test GyT credit parser with real PDF samples"""
        pdf_files = get_sample_pdfs_by_type("gyt", "credit")
        
        for pdf_path in pdf_files[:1]:  # Test first PDF only for unit tests
            parser = GyTCreditParser(pdf_path)
            transactions = parser.extract_data()
            
            # Should return a list
            assert isinstance(transactions, list)
            
            # If transactions found, validate structure
            if transactions:
                transaction = transactions[0]
                assert 'Date' in transaction
                assert 'Description' in transaction
                assert 'Amount' in transaction
                assert 'Transaction Type' in transaction
                assert 'Account Name' in transaction