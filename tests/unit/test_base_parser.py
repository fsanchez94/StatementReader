import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
import pandas as pd
import numpy as np
from src.parsers.base_parser import BaseParser
import tempfile
import os

class MockParser(BaseParser):
    """Mock implementation of BaseParser for testing"""
    def extract_data(self):
        return [
            {
                'Date': date(2024, 1, 15),
                'Description': 'Test Transaction',
                'Original Description': 'Test Transaction Original',
                'Amount': 100.00,
                'Transaction Type': 'Debit',
                'Category': 'Test',
                'Account Name': 'Test Account'
            }
        ]

class TestBaseParser:
    def test_init(self):
        """Test BaseParser initialization"""
        parser = MockParser("test.pdf", is_spouse=True)
        assert parser.pdf_path == "test.pdf"
        assert parser.is_spouse is True
        
        parser2 = MockParser("test2.pdf")
        assert parser2.pdf_path == "test2.pdf"
        assert parser2.is_spouse is False

    def test_convert_to_excel_date(self):
        """Test Excel date conversion"""
        parser = MockParser("test.pdf")
        
        # Test with date object
        test_date = date(2024, 1, 1)
        excel_date = parser._convert_to_excel_date(test_date)
        
        # Excel date should be number of days since 1900-01-01 + 2
        expected = (datetime(2024, 1, 1) - datetime(1900, 1, 1)).days + 2
        assert excel_date == expected
        
        # Test with non-date object (should return as-is)
        non_date = "not a date"
        assert parser._convert_to_excel_date(non_date) == non_date

    def test_to_csv(self):
        """Test CSV export functionality"""
        parser = MockParser("test.pdf")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            temp_path = tmp_file.name
        
        try:
            parser.to_csv(temp_path)
            
            # Verify file was created and has correct content
            assert os.path.exists(temp_path)
            
            # Read back the CSV and verify content
            df = pd.read_csv(temp_path)
            assert len(df) == 1
            assert 'Date' in df.columns
            assert 'Description' in df.columns
            assert 'Amount' in df.columns
            
            # Check that date was converted to Excel format
            assert isinstance(df.iloc[0]['Date'], (int, float, np.integer, np.floating))
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_abstract_method_enforcement(self):
        """Test that BaseParser cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseParser("test.pdf")

    def test_extract_data_called_by_to_csv(self):
        """Test that to_csv properly calls extract_data"""
        parser = MockParser("test.pdf")
        
        with patch.object(parser, 'extract_data') as mock_extract:
            mock_extract.return_value = [
                {
                    'Date': date(2024, 1, 1),
                    'Description': 'Mock Transaction',
                    'Original Description': 'Mock Transaction Original',
                    'Amount': 50.0,
                    'Transaction Type': 'Credit',
                    'Category': 'Mock',
                    'Account Name': 'Mock Account'
                }
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                temp_path = tmp_file.name
            
            try:
                parser.to_csv(temp_path)
                mock_extract.assert_called_once()
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_to_csv_with_empty_data(self):
        """Test CSV export with empty data"""
        parser = MockParser("test.pdf")
        
        with patch.object(parser, 'extract_data') as mock_extract:
            mock_extract.return_value = []
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                temp_path = tmp_file.name
            
            try:
                parser.to_csv(temp_path)
                
                # Verify empty CSV was created
                assert os.path.exists(temp_path)
                # For empty data, check that the file exists but may be empty
                try:
                    df = pd.read_csv(temp_path)
                    assert len(df) == 0
                except pd.errors.EmptyDataError:
                    # If DataFrame was empty, pandas might create an unparseable CSV
                    assert True  # File exists which is what we care about
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_to_csv_without_date_column(self):
        """Test CSV export when data doesn't have Date column"""
        parser = MockParser("test.pdf")
        
        with patch.object(parser, 'extract_data') as mock_extract:
            mock_extract.return_value = [
                {
                    'Description': 'No Date Transaction',
                    'Amount': 25.0
                }
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                temp_path = tmp_file.name
            
            try:
                parser.to_csv(temp_path)
                
                # Should not raise error, just skip date conversion
                df = pd.read_csv(temp_path)
                assert len(df) == 1
                assert 'Date' not in df.columns
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)