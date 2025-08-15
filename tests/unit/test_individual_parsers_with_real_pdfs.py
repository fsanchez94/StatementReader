"""
Tests for individual parsers using real PDF samples
"""
import pytest
import pandas as pd
import sys
import tempfile
import os
from pathlib import Path
from datetime import date

# Add src and fixtures to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent / "fixtures"))

from src.parsers.parser_factory import ParserFactory
from test_data_loader import (
    get_sample_pdfs_by_type, 
    get_expected_output_for_pdf,
    require_sample_pdfs,
    get_all_sample_pdf_combinations,
    has_sample_pdfs
)


class TestParserWithRealPDFs:
    """Test parsers using real PDF samples"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.parametrize("bank_type,account_type,pdf_files", 
                           [combo for combo in get_all_sample_pdf_combinations()])
    def test_parser_extract_data_with_real_pdf(self, bank_type, account_type, pdf_files):
        """Test parser data extraction with real PDF files"""
        for pdf_path in pdf_files:
            # Get parser for this PDF
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            
            # Extract data
            transactions = parser.extract_data()
            
            # Basic validation
            assert isinstance(transactions, list), f"Expected list, got {type(transactions)}"
            
            if transactions:  # Only validate if transactions were found
                # Check transaction structure
                required_fields = ['Date', 'Description', 'Amount', 'Transaction Type', 'Account Name']
                for transaction in transactions:
                    for field in required_fields:
                        assert field in transaction, f"Missing field {field} in transaction"
                    
                    # Validate data types
                    assert isinstance(transaction['Date'], date), "Date should be date object"
                    assert isinstance(transaction['Amount'], (int, float)), "Amount should be numeric"
                    assert transaction['Transaction Type'] in ['credit', 'debit'], "Invalid transaction type"
                    assert isinstance(transaction['Description'], str), "Description should be string"
                    assert isinstance(transaction['Account Name'], str), "Account Name should be string"
    
    @pytest.mark.parametrize("bank_type,account_type,pdf_files", 
                           [combo for combo in get_all_sample_pdf_combinations()])
    def test_parser_to_csv_with_real_pdf(self, bank_type, account_type, pdf_files):
        """Test CSV output generation with real PDF files"""
        for pdf_path in pdf_files:
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            
            # Generate CSV output
            output_path = os.path.join(self.temp_dir, f"test_output_{Path(pdf_path).stem}.csv")
            parser.to_csv(output_path)
            
            # Verify CSV was created
            assert os.path.exists(output_path), f"CSV output not created for {pdf_path}"
            
            # Verify CSV content
            df = pd.read_csv(output_path)
            
            expected_columns = ['Date', 'Description', 'Original Description', 'Amount', 
                              'Transaction Type', 'Category', 'Account Name']
            
            for col in expected_columns:
                assert col in df.columns, f"Missing column {col} in CSV output"
            
            # If we have data, validate it
            if len(df) > 0:
                # Check for non-empty descriptions
                assert not df['Description'].isna().all(), "All descriptions are empty"
                # Check for valid amounts
                assert pd.to_numeric(df['Amount'], errors='coerce').notna().all(), "Invalid amounts found"
                # Check transaction types
                valid_types = ['credit', 'debit']
                assert df['Transaction Type'].isin(valid_types).all(), "Invalid transaction types found"
    
    @pytest.mark.parametrize("bank_type,account_type,pdf_files", 
                           [combo for combo in get_all_sample_pdf_combinations()])
    def test_parser_against_expected_output(self, bank_type, account_type, pdf_files):
        """Test parser output against expected CSV files"""
        for pdf_path in pdf_files:
            expected_csv = get_expected_output_for_pdf(pdf_path)
            
            if not expected_csv:
                pytest.skip(f"No expected output found for {pdf_path}")
            
            # Generate actual output
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            actual_output = os.path.join(self.temp_dir, f"actual_{Path(pdf_path).stem}.csv")
            parser.to_csv(actual_output)
            
            # Load both CSVs
            expected_df = pd.read_csv(expected_csv)
            actual_df = pd.read_csv(actual_output)
            
            # Compare structure
            assert list(expected_df.columns) == list(actual_df.columns), \
                f"Column mismatch for {pdf_path}"
            
            # Compare row count
            assert len(expected_df) == len(actual_df), \
                f"Row count mismatch for {pdf_path}: expected {len(expected_df)}, got {len(actual_df)}"
            
            # Compare key fields (allowing for minor formatting differences)
            if len(expected_df) > 0:
                # Check dates (convert to string for comparison)
                expected_dates = pd.to_datetime(expected_df['Date']).dt.strftime('%Y-%m-%d')
                actual_dates = pd.to_datetime(actual_df['Date']).dt.strftime('%Y-%m-%d')
                assert expected_dates.equals(actual_dates), f"Date mismatch for {pdf_path}"
                
                # Check amounts (within small tolerance for floating point)
                expected_amounts = pd.to_numeric(expected_df['Amount'])
                actual_amounts = pd.to_numeric(actual_df['Amount'])
                assert expected_amounts.round(2).equals(actual_amounts.round(2)), \
                    f"Amount mismatch for {pdf_path}"
                
                # Check descriptions
                assert expected_df['Description'].equals(actual_df['Description']), \
                    f"Description mismatch for {pdf_path}"
    
    @require_sample_pdfs("industrial", "checking")
    def test_industrial_checking_specific_features(self):
        """Test Industrial checking account specific features with real PDFs"""
        pdf_files = get_sample_pdfs_by_type("industrial", "checking")
        
        for pdf_path in pdf_files:
            # Test regular account
            parser = ParserFactory.get_parser("industrial", "checking", pdf_path, is_spouse=False)
            transactions = parser.extract_data()
            
            if transactions:
                assert transactions[0]['Account Name'] == 'Industrial GTQ'
            
            # Test spouse account
            parser_spouse = ParserFactory.get_parser("industrial", "checking", pdf_path, is_spouse=True)
            transactions_spouse = parser_spouse.extract_data()
            
            if transactions_spouse:
                assert transactions_spouse[0]['Account Name'] == 'Industrial GTQ (Spouse)'
    
    @require_sample_pdfs("industrial", "credit")
    def test_industrial_credit_specific_features(self):
        """Test Industrial credit card specific features with real PDFs"""
        pdf_files = get_sample_pdfs_by_type("industrial", "credit")
        
        for pdf_path in pdf_files:
            parser = ParserFactory.get_parser("industrial", "credit", pdf_path)
            transactions = parser.extract_data()
            
            if transactions:
                # Credit card transactions should have account name indicating it's a credit card
                assert 'Credit' in transactions[0]['Account Name'] or 'Industrial' in transactions[0]['Account Name']
    
    def test_error_handling_with_invalid_pdf(self):
        """Test error handling when PDF cannot be processed"""
        # Create a temporary invalid PDF file
        invalid_pdf = os.path.join(self.temp_dir, "invalid.pdf")
        with open(invalid_pdf, 'w') as f:
            f.write("This is not a valid PDF")
        
        parser = ParserFactory.get_parser("industrial", "checking", invalid_pdf)
        
        # Should handle gracefully and return empty list or raise appropriate exception
        try:
            transactions = parser.extract_data()
            assert isinstance(transactions, list), "Should return list even on error"
        except Exception as e:
            # Should be a specific exception, not a generic error
            assert "PDF" in str(e) or "extract" in str(e).lower()
    
    def test_parser_performance_benchmark(self):
        """Basic performance benchmark with real PDFs"""
        import time
        
        combinations = get_all_sample_pdf_combinations()
        if not combinations:
            pytest.skip("No sample PDFs available for performance testing")
        
        total_time = 0
        total_pdfs = 0
        
        for bank_type, account_type, pdf_files in combinations:
            for pdf_path in pdf_files[:2]:  # Test first 2 PDFs of each type
                parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
                
                start_time = time.time()
                transactions = parser.extract_data()
                end_time = time.time()
                
                processing_time = end_time - start_time
                total_time += processing_time
                total_pdfs += 1
                
                # Basic performance expectation: should process within reasonable time
                assert processing_time < 30, f"PDF processing took too long: {processing_time}s for {pdf_path}"
                
                print(f"Processed {Path(pdf_path).name}: {len(transactions)} transactions in {processing_time:.2f}s")
        
        if total_pdfs > 0:
            avg_time = total_time / total_pdfs
            print(f"Average processing time: {avg_time:.2f}s per PDF")


class TestMixedModeTests:
    """Tests that combine mock data with real PDFs for comprehensive coverage"""
    
    def test_mock_vs_real_consistency(self):
        """Compare behavior between mock data and real PDFs where available"""
        # Test with mock data (existing functionality)
        from test_data_loader import get_sample_transaction_lines
        
        mock_lines = get_sample_transaction_lines()
        
        # If we have real PDFs, compare parsing behavior
        combinations = get_all_sample_pdf_combinations()
        
        for bank_type, account_type, pdf_files in combinations:
            if bank_type == "industrial" and account_type == "checking":
                # Test one real PDF
                parser_real = ParserFactory.get_parser(bank_type, account_type, pdf_files[0])
                real_transactions = parser_real.extract_data()
                
                # Test with mock data
                parser_mock = ParserFactory.get_parser(bank_type, account_type, "mock.pdf")
                mock_transactions = parser_mock._parse_page_text(mock_lines)
                
                # Both should return valid transaction structures
                if real_transactions and mock_transactions:
                    real_fields = set(real_transactions[0].keys())
                    mock_fields = set(mock_transactions[0].keys())
                    
                    assert real_fields == mock_fields, "Field structure mismatch between real and mock data"
                
                break  # Only test one combination for this check


# Utility test functions

def test_sample_pdf_availability():
    """Test that sample PDF structure is available and valid"""
    from test_data_loader import validate_sample_pdf_structure
    
    validation = validate_sample_pdf_structure()
    
    # Print status for debugging
    print(f"PDF structure valid: {validation['valid']}")
    if validation['issues']:
        print("Issues found:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    print("PDF Summary:")
    for bank, accounts in validation['summary'].items():
        print(f"  {bank}:")
        for account, count in accounts.items():
            print(f"    {account}: {count} PDFs")
    
    # Test should pass even if no PDFs are available (they're optional)
    # But the structure should be valid
    if not validation['valid']:
        # Only fail if there are structural issues, not just missing PDFs
        structural_issues = [issue for issue in validation['issues'] 
                           if "Missing bank directory" in issue or "Missing account directory" in issue]
        assert not structural_issues, f"Structural issues found: {structural_issues}"


if __name__ == "__main__":
    # Run basic validation
    test_sample_pdf_availability()
    print("PDF sample structure validation passed!")