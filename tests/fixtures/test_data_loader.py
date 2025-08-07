"""
Utility functions for loading test fixtures
"""
import os
import pandas as pd
from pathlib import Path

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