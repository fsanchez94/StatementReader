import pytest
import pandas as pd
import os
import json
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path

# Import the main processing modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from parsers.parser_factory import ParserFactory
from utils.pdf_processor import PDFProcessor

class TestEndToEndProcessing:
    """Integration tests for complete PDF processing pipeline"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_pdf_path = os.path.join(self.temp_dir, "sample.pdf")
        
        # Create a mock PDF file for testing
        with open(self.sample_pdf_path, 'w') as f:
            f.write("mock pdf content")

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('utils.pdf_processor.pdfplumber.open')
    def test_pdf_processor_integration(self, mock_pdfplumber):
        """Test PDFProcessor integration with real-like data"""
        # Setup mock PDF with realistic bank statement content
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        BANCO INDUSTRIAL
        ESTADO DE CUENTA
        FECHA REFERENCIA DESCRIPCIÓN DÉBITO CRÉDITO SALDO
        15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00
        16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00
        """
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor.process(self.sample_pdf_path)
        
        assert "DEPOSITO EFECTIVO" in result
        assert "PAGO SERVICIOS" in result
        assert len(result) > 50  # Should pass validation

    @patch('parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_parser_factory_to_csv_integration(self, mock_pdfplumber):
        """Test complete flow from ParserFactory to CSV output"""
        # Setup mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00
        16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00
        """
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Get parser and process to CSV
        parser = ParserFactory.get_parser("industrial", "checking", self.sample_pdf_path)
        
        output_path = os.path.join(self.temp_dir, "output.csv")
        
        with patch('builtins.print'):  # Suppress print statements
            parser.to_csv(output_path)
        
        # Verify CSV was created and has correct content
        assert os.path.exists(output_path)
        
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'Date' in df.columns
        assert 'Description' in df.columns
        assert 'Amount' in df.columns
        assert 'Transaction Type' in df.columns
        assert 'Account Name' in df.columns
        
        # Check specific transaction data
        assert 'DEPOSITO EFECTIVO' in df['Description'].values
        assert 'PAGO SERVICIOS' in df['Description'].values

    @patch('parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_spouse_account_integration(self, mock_pdfplumber):
        """Test spouse account processing integration"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Test spouse vs non-spouse account naming
        parser_husband = ParserFactory.get_parser("industrial", "checking", self.sample_pdf_path, is_spouse=False)
        parser_spouse = ParserFactory.get_parser("industrial", "checking", self.sample_pdf_path, is_spouse=True)
        
        with patch('builtins.print'):
            transactions_husband = parser_husband.extract_data()
            transactions_spouse = parser_spouse.extract_data()
        
        assert transactions_husband[0]['Account Name'] == 'Industrial GTQ'
        assert transactions_spouse[0]['Account Name'] == 'Industrial GTQ (Spouse)'

    def test_all_supported_parser_types(self):
        """Test that all supported parser types can be instantiated"""
        supported_combinations = [
            ("industrial", "checking"),
            ("industrial", "usd_checking"),
            ("industrial", "credit"),
            ("industrial", "credit_usd"),
            ("bam", "credit"),
            ("gyt", "credit"),
        ]
        
        for bank_type, account_type in supported_combinations:
            parser = ParserFactory.get_parser(bank_type, account_type, self.sample_pdf_path)
            assert parser is not None
            assert parser.pdf_path == self.sample_pdf_path
            assert hasattr(parser, 'extract_data')

    @patch('utils.pdf_processor.pdfplumber.open')
    def test_ocr_fallback_integration(self, mock_pdfplumber):
        """Test OCR fallback integration when text extraction fails"""
        # Setup PDF that returns insufficient text
        mock_page = Mock()
        mock_page.extract_text.return_value = "short"  # Less than 50 chars
        mock_page.to_image.return_value = Mock()
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Mock OCR components
        with patch('utils.pdf_processor.pytesseract.image_to_string') as mock_ocr:
            with patch('utils.pdf_processor.Image.open'):
                mock_ocr.return_value = "This is a long OCR result that should pass validation and contains bank data"
                
                processor = PDFProcessor()
                result = processor.process(self.sample_pdf_path)
                
                assert result == "This is a long OCR result that should pass validation and contains bank data"
                mock_ocr.assert_called_once()

    def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        # Test with non-existent file
        with pytest.raises(Exception):
            processor = PDFProcessor()
            processor.process("/non/existent/file.pdf")
        
        # Test with invalid bank/account combination
        with pytest.raises(ValueError):
            ParserFactory.get_parser("invalid_bank", "checking", self.sample_pdf_path)

    @patch('parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_csv_format_consistency(self, mock_pdfplumber):
        """Test that CSV output format is consistent across different parsers"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "15/01/2024 123456 TEST TRANSACTION 100.00 1,000.00"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        expected_columns = ['Date', 'Description', 'Original Description', 'Amount', 
                          'Transaction Type', 'Category', 'Account Name']
        
        # Test multiple parser types have consistent CSV format
        parser_types = [("industrial", "checking")]  # Add more as needed
        
        for bank_type, account_type in parser_types:
            parser = ParserFactory.get_parser(bank_type, account_type, self.sample_pdf_path)
            
            output_path = os.path.join(self.temp_dir, f"test_{bank_type}_{account_type}.csv")
            
            with patch('builtins.print'):
                parser.to_csv(output_path)
            
            df = pd.read_csv(output_path)
            
            # Check that all expected columns are present
            for col in expected_columns:
                assert col in df.columns, f"Missing column {col} in {bank_type}_{account_type}"

    def test_date_conversion_consistency(self):
        """Test that date conversion is consistent across the system"""
        from parsers.base_parser import BaseParser
        from datetime import date
        
        # Create mock parser to test date conversion
        class MockParser(BaseParser):
            def extract_data(self):
                return [{'Date': date(2024, 1, 15), 'Amount': 100}]
        
        parser = MockParser("test.pdf")
        
        # Test Excel date conversion
        test_date = date(2024, 1, 15)
        excel_date = parser._convert_to_excel_date(test_date)
        
        # Verify the conversion is consistent with mainbundlev2.py logic
        from datetime import datetime
        expected = (datetime.combine(test_date, datetime.min.time()) - datetime(1900, 1, 1)).days + 2
        
        assert excel_date == expected

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_batch_processing_integration(self, mock_listdir, mock_exists):
        """Test batch processing functionality"""
        # Mock file system for batch processing
        mock_exists.return_value = True
        mock_listdir.return_value = ['file1.pdf', 'file2.pdf', 'not_a_pdf.txt']
        
        # Import and test the get_pdf_files function from mainbundlev2
        sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
        from mainbundlev2 import get_pdf_files
        
        pdf_files = get_pdf_files("/mock/folder")
        
        # Should only return PDF files
        assert len(pdf_files) == 2
        assert all(f.endswith('.pdf') for f in pdf_files)