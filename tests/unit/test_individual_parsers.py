import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from src.parsers.banco_industrial_checking_parser import BancoIndustrialCheckingParser
from src.parsers.banco_industrial_credit_parser import BancoIndustrialCreditParser
from src.parsers.bam_credit_parser import BAMCreditParser
from src.parsers.gyt_credit_parser import GyTCreditParser

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

    def test_parse_valid_transaction_line(self):
        """Test parsing a valid transaction line"""
        lines = ["15/01/2024 123456 PAGO TARJETA DE CREDITO 1,500.00 5,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction['Date'] == date(2024, 1, 15)
        assert transaction['Description'] == 'PAGO TARJETA DE CREDITO'
        assert transaction['Original Description'] == 'PAGO TARJETA DE CREDITO'
        assert transaction['Amount'] == 1500.00
        assert transaction['Transaction Type'] == 'credit'
        assert transaction['Account Name'] == 'Industrial GTQ'
        assert transaction['Category'] == ''

    def test_parse_transaction_line_spouse_account(self):
        """Test parsing transaction for spouse account"""
        lines = ["15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"]
        
        transactions = self.parser_spouse._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Account Name'] == 'Industrial GTQ (Spouse)'

    def test_parse_multiple_transactions(self):
        """Test parsing multiple transaction lines"""
        lines = [
            "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00",
            "16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00"
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 2
        
        # First transaction (credit - balance increased from 1500 to 2000)
        assert transactions[0]['Transaction Type'] == 'credit'
        assert transactions[0]['Amount'] == 500.00
        
        # Second transaction (debit - balance decreased from 2000 to 1800)
        assert transactions[1]['Transaction Type'] == 'debit'
        assert transactions[1]['Amount'] == -200.00

    def test_skip_summary_lines(self):
        """Test that summary lines are skipped"""
        lines = [
            "SUBTOTAL DE CREDITOS 1,500.00",
            "TOTAL DE DEBITOS 500.00",
            "SALDO ANTERIOR 1,000.00",
            "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00",
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
            "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"
        ]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    def test_parse_line_without_reference_number(self):
        """Test parsing line without reference number"""
        lines = ["15/01/2024 DEPOSITO EFECTIVO 500.00 2,000.00"]
        
        transactions = self.parser._parse_page_text(lines)
        
        assert len(transactions) == 1
        assert transactions[0]['Description'] == 'DEPOSITO EFECTIVO'

    def test_parse_line_with_comma_in_amounts(self):
        """Test parsing line with comma-separated amounts"""
        lines = ["15/01/2024 123456 DEPOSITO GRANDE 1,500.50 10,000.75"]
        
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
            "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"  # Valid line
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
15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00
16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00"""
        
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
        mock_page1.extract_text.return_value = "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        with patch('builtins.print'):
            transactions = self.parser.extract_data()
        
        assert len(transactions) == 2


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