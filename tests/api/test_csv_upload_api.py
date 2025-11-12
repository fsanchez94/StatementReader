"""
Integration tests for CSV upload API endpoints
Tests file upload, validation, detection, and processing of CSV files
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from io import BytesIO

# Add Django backend to path
backend_path = Path(__file__).parent.parent.parent / "backends" / "django"
sys.path.insert(0, str(backend_path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_parser_project.settings')

import django
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from parser_api.models import ProcessingSession, UploadedFile
from parser_api.views import validate_csv_file, detect_csv_bank_type


class TestCSVValidation:
    """Test CSV validation function"""

    @pytest.fixture
    def valid_csv_content(self):
        return """Tipo de Transacciones,
,DE = Depósito,,,CQ = Pago de Cheque,
,NC = Nota de Crédito,,,ND = Nota de Débito,

Cuenta: 3140014105 - SANCHEZ LIU JOSE FELIPE
Saldo inicial (Q.): 13583.60
Del 01/10/2025 al 31/10/2025

Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST TRANSACTION,1173336,,1500.00,15083.60
"""

    @pytest.fixture
    def valid_csv_file(self, tmp_path, valid_csv_content):
        csv_file = tmp_path / "valid.csv"
        csv_file.write_text(valid_csv_content, encoding='utf-16-be')
        return str(csv_file)

    def test_validate_valid_csv(self, valid_csv_file):
        """Test validation passes for valid CSV"""
        result = validate_csv_file(valid_csv_file)
        assert result is True

    def test_validate_missing_header(self, tmp_path):
        """Test validation fails for CSV without proper header"""
        content = """Some random content
Without proper structure
"""
        csv_file = tmp_path / "no_header.csv"
        csv_file.write_text(content, encoding='utf-8')

        with pytest.raises(ValueError, match="Could not find header row"):
            validate_csv_file(str(csv_file))

    def test_validate_missing_date_range(self, tmp_path):
        """Test validation fails for CSV without date range"""
        content = """Tipo de Transacciones,
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "no_date.csv"
        csv_file.write_text(content, encoding='utf-8')

        with pytest.raises(ValueError, match="Missing date range line"):
            validate_csv_file(str(csv_file))

    def test_validate_missing_columns(self, tmp_path):
        """Test validation fails for CSV with missing required columns"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc
01- 10,NC,TEST,123
"""
        csv_file = tmp_path / "missing_cols.csv"
        csv_file.write_text(content, encoding='utf-8')

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_csv_file(str(csv_file))


class TestCSVAutoDetection:
    """Test CSV auto-detection function"""

    @pytest.fixture
    def gtq_csv_file(self, tmp_path):
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "gtq.csv"
        csv_file.write_text(content, encoding='utf-16-be')
        return str(csv_file)

    @pytest.fixture
    def usd_csv_file(self, tmp_path):
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (USD),Haber (USD),Saldo (USD)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_file = tmp_path / "usd.csv"
        csv_file.write_text(content, encoding='utf-16-be')
        return str(csv_file)

    def test_detect_gtq_checking(self, gtq_csv_file):
        """Test detection of GTQ checking account CSV"""
        bank_type, account_type = detect_csv_bank_type(gtq_csv_file)
        assert bank_type == 'industrial'
        assert account_type == 'checking'

    def test_detect_usd_checking(self, usd_csv_file):
        """Test detection of USD checking account CSV"""
        bank_type, account_type = detect_csv_bank_type(usd_csv_file)
        assert bank_type == 'industrial'
        assert account_type == 'usd_checking'

    def test_detect_invalid_csv(self, tmp_path):
        """Test detection returns None for invalid CSV"""
        content = "This is not a valid BI CSV file"
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text(content, encoding='utf-8')

        bank_type, account_type = detect_csv_bank_type(str(csv_file))
        assert bank_type is None
        assert account_type is None


class TestCSVUploadEndpoint:
    """Test CSV file upload through Django API"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for upload testing"""
        content = """Tipo de Transacciones,
,DE = Depósito,,,CQ = Pago de Cheque,
,NC = Nota de Crédito,,,ND = Nota de Débito,

Cuenta: 3140014105 - TEST ACCOUNT
Saldo inicial (Q.): 1000.00
Del 01/10/2025 al 31/10/2025

Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,DEPOSIT TEST,1001,,500.00,1500.00
02- 10,ND,WITHDRAWAL TEST,1002,200.00,,1300.00
"""
        # Encode as UTF-16 BE like real files
        csv_bytes = content.encode('utf-16-be')
        return SimpleUploadedFile(
            "test_statement.csv",
            csv_bytes,
            content_type="text/csv"
        )

    def test_upload_csv_file(self, client, sample_csv_file):
        """Test uploading a CSV file creates a session"""
        response = client.post(
            '/api/upload/',
            {
                'files': [sample_csv_file],
                'parsers': '{}'
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert 'session_id' in data
        assert data['total_files'] == 1

        # Verify file record was created with correct file_type
        session = ProcessingSession.objects.get(session_id=data['session_id'])
        uploaded_file = session.files.first()
        assert uploaded_file is not None
        assert uploaded_file.file_type == 'csv'
        assert uploaded_file.filename == 'test_statement.csv'

    def test_upload_mixed_files(self, client, sample_csv_file):
        """Test uploading both PDF and CSV files in same session"""
        # Create a dummy PDF file
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        response = client.post(
            '/api/upload/',
            {
                'files': [sample_csv_file, pdf_file],
                'parsers': '{}'
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['total_files'] == 2

        # Verify file types are correct
        session = ProcessingSession.objects.get(session_id=data['session_id'])
        files = list(session.files.all())
        file_types = {f.filename: f.file_type for f in files}

        assert file_types['test_statement.csv'] == 'csv'
        assert file_types['test.pdf'] == 'pdf'


class TestCSVDetectionEndpoint:
    """Test CSV auto-detection through API"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def uploaded_csv_session(self, client):
        """Create a session with uploaded CSV file"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,TEST,123,,100.00,100.00
"""
        csv_bytes = content.encode('utf-16-be')
        csv_file = SimpleUploadedFile(
            "bi_gtq_statement.csv",
            csv_bytes,
            content_type="text/csv"
        )

        response = client.post(
            '/api/upload/',
            {'files': [csv_file], 'parsers': '{}'}
        )
        return response.json()['session_id']

    def test_detect_csv_parser_type(self, client, uploaded_csv_session):
        """Test auto-detection API endpoint for CSV files"""
        response = client.post(f'/api/detect-parser/{uploaded_csv_session}/')

        assert response.status_code == 200
        data = response.json()

        # Should have detected the CSV file
        assert 'bi_gtq_statement.csv' in data
        suggestion = data['bi_gtq_statement.csv']

        assert suggestion['suggested'] is not None
        assert suggestion['suggested']['bank'] == 'industrial'
        assert suggestion['suggested']['account'] == 'checking'
        assert suggestion['error'] is None


class TestCSVProcessingEndpoint:
    """Test CSV processing through API"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def csv_session_ready_to_process(self, client):
        """Create a session with CSV file ready to process"""
        content = """Tipo de Transacciones,
Del 01/10/2025 al 31/10/2025
Fecha,TT,Descripción,No. Doc,Debe (Q.),Haber (Q.),Saldo (Q.)
01- 10,NC,INCOME DEPOSIT,1001,,1000.00,1000.00
02- 10,ND,STORE PURCHASE,1002,50.00,,950.00
03- 10,NC,REFUND,1003,,25.00,975.00
"""
        csv_bytes = content.encode('utf-16-be')
        csv_file = SimpleUploadedFile(
            "process_test.csv",
            csv_bytes,
            content_type="text/csv"
        )

        # Upload file
        response = client.post(
            '/api/upload/',
            {'files': [csv_file], 'parsers': '{}'}
        )
        session_id = response.json()['session_id']

        # Update parser selection
        client.post(
            f'/api/update-parsers/{session_id}/',
            {
                'parsers': {
                    'process_test.csv': {
                        'bank': 'industrial',
                        'account': 'checking'
                    }
                }
            },
            content_type='application/json'
        )

        return session_id

    def test_process_csv_file(self, client, csv_session_ready_to_process):
        """Test processing a CSV file extracts transactions"""
        session_id = csv_session_ready_to_process

        response = client.post(f'/api/process/{session_id}/')

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'completed'
        assert data['processed_files'] == 1

        # Verify transactions were saved
        session = ProcessingSession.objects.get(session_id=session_id)
        transactions = session.transactions.all()

        assert transactions.count() == 3

        # Verify transaction details
        transaction_types = [t.transaction_type for t in transactions]
        assert 'credit' in transaction_types
        assert 'debit' in transaction_types

        # Verify amounts
        amounts = [float(t.amount) for t in transactions]
        assert 1000.00 in amounts  # First credit
        assert 50.00 in amounts    # Debit
        assert 25.00 in amounts    # Second credit


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
