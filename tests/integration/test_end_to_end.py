import pytest
import pandas as pd
import os
import json
import tempfile
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Import the main processing modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent / "fixtures"))

from src.parsers.parser_factory import ParserFactory
from src.utils.pdf_processor import PDFProcessor

# Import real PDF testing utilities
try:
    from test_data_loader import (
        get_sample_pdfs_by_type, 
        get_expected_output_for_pdf,
        require_sample_pdfs,
        get_all_sample_pdf_combinations,
        has_sample_pdfs
    )
    REAL_PDF_TESTING_AVAILABLE = True
except ImportError:
    REAL_PDF_TESTING_AVAILABLE = False

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

    @patch('src.utils.pdf_processor.pdfplumber.open')
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
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor.process(self.sample_pdf_path)
        
        assert "DEPOSITO EFECTIVO" in result
        assert "PAGO SERVICIOS" in result
        assert len(result) > 50  # Should pass validation

    @patch('src.parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_parser_factory_to_csv_integration(self, mock_pdfplumber):
        """Test complete flow from ParserFactory to CSV output"""
        # Setup mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00
        16/01/2024 123457 PAGO SERVICIOS 200.00 1,800.00
        """
        
        mock_pdf = MagicMock()
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

    @patch('src.parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_spouse_account_integration(self, mock_pdfplumber):
        """Test spouse account processing integration"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "15/01/2024 123456 DEPOSITO EFECTIVO 500.00 2,000.00"
        
        mock_pdf = MagicMock()
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

    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_ocr_fallback_integration(self, mock_pdfplumber):
        """Test OCR fallback integration when text extraction fails"""
        # Setup PDF that returns insufficient text
        mock_page = Mock()
        mock_page.extract_text.return_value = "short"  # Less than 50 chars
        mock_page.to_image.return_value = Mock()
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Mock OCR components
        with patch('src.utils.pdf_processor.pytesseract.image_to_string') as mock_ocr:
            with patch('src.utils.pdf_processor.Image.open'):
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

    @patch('src.parsers.banco_industrial_checking_parser.pdfplumber.open')
    def test_csv_format_consistency(self, mock_pdfplumber):
        """Test that CSV output format is consistent across different parsers"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "15/01/2024 123456 TEST TRANSACTION 100.00 1,000.00"
        
        mock_pdf = MagicMock()
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
        from src.parsers.base_parser import BaseParser
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
        from src.mainbundlev2 import get_pdf_files
        
        pdf_files = get_pdf_files("/mock/folder")
        
        # Should only return PDF files
        assert len(pdf_files) == 2
        assert all(f.endswith('.pdf') for f in pdf_files)


@pytest.mark.skipif(not REAL_PDF_TESTING_AVAILABLE, reason="Real PDF testing not available")
class TestRealPDFIntegration:
    """Integration tests using real PDF files"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.parametrize("bank_type,account_type,pdf_files", 
                           [combo for combo in get_all_sample_pdf_combinations() if combo])
    def test_complete_pipeline_with_real_pdfs(self, bank_type, account_type, pdf_files):
        """Test complete processing pipeline with real PDF files"""
        for pdf_path in pdf_files[:2]:  # Test first 2 PDFs of each type
            # Step 1: PDF Processing
            processor = PDFProcessor()
            extracted_text = processor.process(pdf_path)
            
            # Should extract some text
            assert isinstance(extracted_text, str)
            assert len(extracted_text) > 0
            
            # Step 2: Parser creation and data extraction
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            transactions = parser.extract_data()
            
            # Should return a list
            assert isinstance(transactions, list)
            
            # Step 3: CSV generation
            output_path = os.path.join(self.temp_dir, f"output_{Path(pdf_path).stem}.csv")
            parser.to_csv(output_path)
            
            # Should create CSV file
            assert os.path.exists(output_path)
            
            # Step 4: CSV validation
            df = pd.read_csv(output_path)
            expected_columns = ['Date', 'Description', 'Original Description', 'Amount', 
                              'Transaction Type', 'Category', 'Account Name']
            
            for col in expected_columns:
                assert col in df.columns, f"Missing column {col}"
            
            # If we have transactions, validate their structure
            if len(df) > 0:
                # Check date format
                dates = pd.to_datetime(df['Date'], errors='coerce')
                assert not dates.isna().any(), "Invalid dates found"
                
                # Check amounts are numeric
                amounts = pd.to_numeric(df['Amount'], errors='coerce')
                assert not amounts.isna().any(), "Invalid amounts found"
                
                # Check transaction types
                valid_types = ['credit', 'debit']
                assert df['Transaction Type'].isin(valid_types).all(), "Invalid transaction types"
                
                # Check descriptions are not empty
                assert not df['Description'].str.strip().eq('').any(), "Empty descriptions found"
    
    @pytest.mark.parametrize("bank_type,account_type,pdf_files", 
                           [combo for combo in get_all_sample_pdf_combinations() if combo])
    def test_real_pdf_against_expected_output(self, bank_type, account_type, pdf_files):
        """Test real PDF processing against expected outputs"""
        for pdf_path in pdf_files:
            expected_csv = get_expected_output_for_pdf(pdf_path)
            
            if not expected_csv:
                pytest.skip(f"No expected output available for {pdf_path}")
            
            # Process PDF
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            actual_output = os.path.join(self.temp_dir, f"actual_{Path(pdf_path).stem}.csv")
            parser.to_csv(actual_output)
            
            # Load and compare
            expected_df = pd.read_csv(expected_csv)
            actual_df = pd.read_csv(actual_output)
            
            # Structure comparison
            assert list(expected_df.columns) == list(actual_df.columns), \
                f"Column structure mismatch for {pdf_path}"
            
            assert len(expected_df) == len(actual_df), \
                f"Transaction count mismatch for {pdf_path}"
            
            # Content comparison (if not empty)
            if len(expected_df) > 0:
                # Compare key fields with tolerance for formatting differences
                expected_amounts = expected_df['Amount'].round(2)
                actual_amounts = actual_df['Amount'].round(2)
                assert expected_amounts.equals(actual_amounts), \
                    f"Amount mismatch for {pdf_path}"
                
                assert expected_df['Description'].equals(actual_df['Description']), \
                    f"Description mismatch for {pdf_path}"
    
    @require_sample_pdfs("industrial", "checking")
    def test_spouse_account_processing_real_pdf(self):
        """Test spouse account processing with real Industrial checking PDFs"""
        pdf_files = get_sample_pdfs_by_type("industrial", "checking")
        
        for pdf_path in pdf_files[:1]:  # Test first PDF
            # Regular account
            parser_regular = ParserFactory.get_parser("industrial", "checking", pdf_path, is_spouse=False)
            transactions_regular = parser_regular.extract_data()
            
            # Spouse account
            parser_spouse = ParserFactory.get_parser("industrial", "checking", pdf_path, is_spouse=True)
            transactions_spouse = parser_spouse.extract_data()
            
            # Should have same number of transactions
            assert len(transactions_regular) == len(transactions_spouse)
            
            # Account names should be different
            if transactions_regular and transactions_spouse:
                assert transactions_regular[0]['Account Name'] == 'Industrial GTQ'
                assert transactions_spouse[0]['Account Name'] == 'Industrial GTQ (Spouse)'
                
                # Other fields should be identical
                for i, (reg, spouse) in enumerate(zip(transactions_regular, transactions_spouse)):
                    assert reg['Date'] == spouse['Date'], f"Date mismatch at transaction {i}"
                    assert reg['Amount'] == spouse['Amount'], f"Amount mismatch at transaction {i}"
                    assert reg['Description'] == spouse['Description'], f"Description mismatch at transaction {i}"
    
    def test_pdf_processor_performance_real_files(self):
        """Test PDF processor performance with real files"""
        import time
        
        combinations = get_all_sample_pdf_combinations()
        if not combinations:
            pytest.skip("No sample PDFs available for performance testing")
        
        processor = PDFProcessor()
        total_time = 0
        total_files = 0
        
        for bank_type, account_type, pdf_files in combinations:
            for pdf_path in pdf_files[:1]:  # Test first PDF of each type
                start_time = time.time()
                result = processor.process(pdf_path)
                end_time = time.time()
                
                processing_time = end_time - start_time
                total_time += processing_time
                total_files += 1
                
                # Should process within reasonable time
                assert processing_time < 30, f"PDF processing too slow: {processing_time}s for {pdf_path}"
                
                # Should return meaningful content
                assert len(result) > 50, f"Insufficient content extracted from {pdf_path}"
        
        if total_files > 0:
            avg_time = total_time / total_files
            print(f"Average PDF processing time: {avg_time:.2f}s")
            # Performance benchmark: should average less than 10 seconds per PDF
            assert avg_time < 10, f"Average processing time too slow: {avg_time}s"
    
    def test_error_handling_with_real_structure(self):
        """Test error handling with real directory structure but corrupted files"""
        # Test with directory structure but no actual PDFs
        combinations = get_all_sample_pdf_combinations()
        
        if combinations:
            # Test with first available bank/account type
            bank_type, account_type, _ = combinations[0]
            
            # Try to create parser with non-existent file in correct structure
            non_existent_pdf = f"tests/fixtures/sample_pdfs/{bank_type}/{account_type}/non_existent.pdf"
            
            # Should handle gracefully
            try:
                parser = ParserFactory.get_parser(bank_type, account_type, non_existent_pdf)
                transactions = parser.extract_data()
                # Should return empty list or handle gracefully
                assert isinstance(transactions, list)
            except FileNotFoundError:
                # This is acceptable behavior
                pass
            except Exception as e:
                # Should not raise unexpected exceptions
                assert "PDF" in str(e) or "file" in str(e).lower(), f"Unexpected error: {e}"
    
    def test_mixed_bank_types_processing(self):
        """Test processing PDFs from different banks in sequence"""
        combinations = get_all_sample_pdf_combinations()
        
        if len(combinations) < 2:
            pytest.skip("Need at least 2 different bank types for this test")
        
        all_results = []
        
        for bank_type, account_type, pdf_files in combinations:
            for pdf_path in pdf_files[:1]:  # One PDF per bank type
                parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
                transactions = parser.extract_data()
                
                output_path = os.path.join(self.temp_dir, f"{bank_type}_{account_type}_output.csv")
                parser.to_csv(output_path)
                
                df = pd.read_csv(output_path)
                all_results.append({
                    'bank_type': bank_type,
                    'account_type': account_type,
                    'transaction_count': len(df),
                    'csv_path': output_path
                })
        
        # Should have processed multiple bank types
        bank_types_processed = set(result['bank_type'] for result in all_results)
        assert len(bank_types_processed) >= 2, "Should process multiple bank types"
        
        # All CSV files should exist and be valid
        for result in all_results:
            assert os.path.exists(result['csv_path'])
            df = pd.read_csv(result['csv_path'])
            
            # Should have consistent column structure across banks
            expected_columns = ['Date', 'Description', 'Original Description', 'Amount', 
                              'Transaction Type', 'Category', 'Account Name']
            assert list(df.columns) == expected_columns