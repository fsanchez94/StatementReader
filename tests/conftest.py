import pytest
import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_pdf_path():
    """Return path to a sample PDF file for testing"""
    return Path(__file__).parent / "fixtures" / "sample_statement.pdf"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return [
        {
            'Date': '2024-01-15',
            'Description': 'PAGO TARJETA DE CREDITO',
            'Original Description': 'PAGO TARJETA DE CREDITO BANCO INDUSTRIAL',
            'Amount': 1000.00,
            'Transaction Type': 'Debit',
            'Category': 'Payment',
            'Account Name': 'Test Account'
        },
        {
            'Date': '2024-01-16',
            'Description': 'DEPOSITO EFECTIVO',
            'Original Description': 'DEPOSITO EN EFECTIVO ATM',
            'Amount': 500.00,
            'Transaction Type': 'Credit',
            'Category': 'Deposit',
            'Account Name': 'Test Account'
        }
    ]