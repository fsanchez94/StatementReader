"""
Utility functions for loading test fixtures
"""
import os
import pandas as pd
from pathlib import Path
import glob
import pytest

def get_fixtures_dir():
    """Get the fixtures directory path"""
    return Path(__file__).parent

def load_sample_text_data(filename):
    """Load sample text data from fixtures"""
    fixtures_dir = get_fixtures_dir()
    file_path = fixtures_dir / filename
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_expected_csv(filename):
    """Load expected CSV output from fixtures"""
    fixtures_dir = get_fixtures_dir()
    file_path = fixtures_dir / filename
    
    return pd.read_csv(file_path)

def get_sample_transaction_lines():
    """Get sample transaction lines for testing parsers"""
    return [
        "05/01/2024 123456 DEPOSITO EFECTIVO ATM 2,000.00 12,000.00",
        "10/01/2024 123457 PAGO TARJETA DE CREDITO 1,500.00 10,500.00",
        "15/01/2024 123458 TRANSFERENCIA RECIBIDA 5,000.00 15,500.00",
        "20/01/2024 123459 PAGO SERVICIOS PUBLICOS 800.00 14,700.00",
        "25/01/2024 123460 COMISION MANTENIMIENTO 25.00 14,675.00",
        "30/01/2024 123461 DEPOSITO EFECTIVO 1,000.00 15,675.00"
    ]

def get_sample_credit_lines():
    """Get sample credit card transaction lines"""
    return [
        "03/01/2024 TXN001 SUPERMERCADO LA TORRE 150.00 -650.00",
        "07/01/2024 TXN002 GASOLINERA PUMA 75.00 -725.00",
        "12/01/2024 PAY001 PAGO RECIBIDO 800.00 75.00",
        "18/01/2024 TXN003 RESTAURANTE SAZON 85.00 -10.00"
    ]

def get_invalid_lines():
    """Get sample invalid lines that should be skipped"""
    return [
        "SUBTOTAL CREDITOS 8,000.00",
        "TOTAL DEBITOS 2,325.00",
        "SALDO ANTERIOR 10,000.00",
        "SALDO ACTUAL 15,675.00",
        "FECHA REFERENCIA DESCRIPCIÓN DÉBITO CRÉDITO SALDO",
        "This is not a transaction line",
        "Invalid date format: 2024/01/15 DEPOSIT 100.00"
    ]

def create_mock_pdf_content(transaction_lines):
    """Create mock PDF content with headers and transaction lines"""
    header = """BANCO INDUSTRIAL DE GUATEMALA
ESTADO DE CUENTA
FECHA REFERENCIA DESCRIPCIÓN DÉBITO CRÉDITO SALDO"""
    
    footer = """SUBTOTAL CREDITOS 8,000.00
SUBTOTAL DEBITOS 2,325.00
SALDO FINAL 15,675.00"""
    
    content_lines = [header] + transaction_lines + [footer]
    return '\n'.join(content_lines)

# Real PDF loading functions

def get_sample_pdfs_dir():
    """Get the sample PDFs directory path"""
    return get_fixtures_dir() / "sample_pdfs"

def get_expected_outputs_dir():
    """Get the expected outputs directory path"""
    return get_fixtures_dir() / "expected_outputs"

def get_sample_pdfs_by_type(bank_type, account_type):
    """Get list of sample PDF files for a specific bank and account type
    
    Args:
        bank_type (str): Bank type (e.g., 'industrial', 'bam', 'gyt')
        account_type (str): Account type (e.g., 'checking', 'credit', 'usd_checking')
    
    Returns:
        list: List of PDF file paths
    """
    pdfs_dir = get_sample_pdfs_dir() / bank_type / account_type
    
    if not pdfs_dir.exists():
        return []
    
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    return [str(pdf_path) for pdf_path in pdf_files]

def get_expected_output_for_pdf(pdf_path):
    """Get expected CSV output file path for a given PDF
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Path to expected CSV file, or None if not found
    """
    pdf_path = Path(pdf_path)
    pdf_name = pdf_path.stem  # filename without extension
    
    # Extract bank type from path (e.g., industrial, bam, gyt)
    path_parts = pdf_path.parts
    sample_pdfs_index = next(i for i, part in enumerate(path_parts) if part == "sample_pdfs")
    bank_type = path_parts[sample_pdfs_index + 1]
    
    expected_csv_path = get_expected_outputs_dir() / bank_type / f"{pdf_name}.csv"
    
    return str(expected_csv_path) if expected_csv_path.exists() else None

def has_sample_pdfs(bank_type, account_type):
    """Check if sample PDFs are available for testing
    
    Args:
        bank_type (str): Bank type
        account_type (str): Account type
    
    Returns:
        bool: True if sample PDFs are available
    """
    return len(get_sample_pdfs_by_type(bank_type, account_type)) > 0

def require_sample_pdfs(bank_type, account_type):
    """Decorator/function to skip tests if sample PDFs are not available
    
    Args:
        bank_type (str): Bank type
        account_type (str): Account type
    
    Returns:
        pytest.mark.skipif decorator
    """
    return pytest.mark.skipif(
        not has_sample_pdfs(bank_type, account_type),
        reason=f"No sample PDFs available for {bank_type} {account_type}"
    )

def get_all_sample_pdf_combinations():
    """Get all available bank_type, account_type combinations that have sample PDFs
    
    Returns:
        list: List of tuples (bank_type, account_type, pdf_files)
    """
    combinations = []
    pdfs_dir = get_sample_pdfs_dir()
    
    if not pdfs_dir.exists():
        return combinations
    
    for bank_dir in pdfs_dir.iterdir():
        if bank_dir.is_dir():
            bank_type = bank_dir.name
            for account_dir in bank_dir.iterdir():
                if account_dir.is_dir():
                    account_type = account_dir.name
                    pdf_files = get_sample_pdfs_by_type(bank_type, account_type)
                    if pdf_files:
                        combinations.append((bank_type, account_type, pdf_files))
    
    return combinations

def validate_sample_pdf_structure():
    """Validate that sample PDF directory structure is correct
    
    Returns:
        dict: Validation results with any issues found
    """
    results = {
        'valid': True,
        'issues': [],
        'summary': {}
    }
    
    expected_structure = {
        'industrial': ['checking', 'usd_checking', 'credit', 'credit_usd'],
        'bam': ['credit'],
        'gyt': ['credit']
    }
    
    pdfs_dir = get_sample_pdfs_dir()
    
    if not pdfs_dir.exists():
        results['valid'] = False
        results['issues'].append(f"Sample PDFs directory does not exist: {pdfs_dir}")
        return results
    
    for bank_type, account_types in expected_structure.items():
        bank_dir = pdfs_dir / bank_type
        if not bank_dir.exists():
            results['issues'].append(f"Missing bank directory: {bank_type}")
            continue
            
        results['summary'][bank_type] = {}
        
        for account_type in account_types:
            account_dir = bank_dir / account_type
            if not account_dir.exists():
                results['issues'].append(f"Missing account directory: {bank_type}/{account_type}")
                continue
            
            pdf_count = len(list(account_dir.glob("*.pdf")))
            results['summary'][bank_type][account_type] = pdf_count
            
            if pdf_count == 0:
                results['issues'].append(f"No PDF files in: {bank_type}/{account_type}")
    
    if results['issues']:
        results['valid'] = False
    
    return results