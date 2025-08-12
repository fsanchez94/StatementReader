# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PDF Bank Statement Parser that converts bank statement PDFs into structured CSV and Excel files. The system supports multiple Guatemalan banks (Banco Industrial, BAM, GyT) and different account types (checking, credit cards, USD accounts).

## Installation and Setup

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Required system dependency:
- Tesseract OCR must be installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` for Windows

## Common Commands

### Web Application (Recommended)
Start the Django backend:
```bash
python scripts/run_django.py
```

Start the React frontend (in separate terminal):
```bash
cd frontend && npm start
```

Access the application at: http://localhost:3000

### Django Admin
Create admin user:
```bash
python scripts/create_admin_user.py
```
Access Django admin at: http://127.0.0.1:5000/admin/

### Command Line Processing (Legacy)
Run single PDF processing (interactive):
```bash
python src/main.py
```

Run batch processing (multiple PDFs, interactive):
```bash
python src/mainbundlev2.py
```
Note: This script reads folder paths from `config.json`. To change paths, edit the config file:
```json
{
    "paths": {
        "husband_folder": "path/to/husband/pdfs",
        "spouse_folder": "path/to/spouse/pdfs"
    }
}
```

## Architecture

### Core Components

- **Parser Factory Pattern**: `src/parsers/parser_factory.py` creates appropriate parsers based on bank and account type
- **Base Parser**: `src/parsers/base_parser.py` defines the abstract interface all parsers implement
- **PDF Processing**: `src/utils/pdf_processor.py` handles PDF text extraction with OCR fallback

### Parser Types

Supported bank/account combinations:
- `industrial` + `checking`: Banco Industrial GTQ checking accounts
- `industrial` + `usd_checking`: Banco Industrial USD checking accounts  
- `industrial` + `credit`: Banco Industrial credit cards
- `industrial` + `credit_usd`: Banco Industrial USD credit cards
- `bam` + `credit`: BAM credit cards
- `gyt` + `credit`: GyT credit cards

### Data Flow

1. PDF input → PDFProcessor extracts text (with OCR fallback)
2. ParserFactory selects appropriate parser based on bank/account type
3. Parser extracts transactions using bank-specific patterns
4. Data exported to CSV/Excel with standardized columns

### Output Formats

**Individual CSV files** (per PDF): Date, Description, Original Description, Amount, Transaction Type, Category, Account Name

**Combined CSV file**: Date, Description, Original Description, Amount, Transaction Type, Category, Account Name, Labels, Notes

Note: `mainbundlev2.py` processes separate husband/spouse folders and creates individual CSV files plus a combined `all_transactions_YYYYMMDD.csv` file.

## Project Structure

```
pdf_bank_parser/
├── backends/               # Backend implementations
│   ├── django/            # Django REST API (primary)
│   └── legacy/            # Flask API (legacy)
├── frontend/              # React web application
│   ├── src/              # React components and services
│   └── public/           # Static assets
├── src/                   # Core parsing engine
│   ├── main.py           # Single PDF processor (CLI)
│   ├── mainbundlev2.py   # Batch processor (CLI)
│   ├── parsers/          # Bank-specific parsers
│   └── utils/            # PDF processing utilities
├── scripts/               # Management and utility scripts
│   ├── run_django.py     # Start Django server
│   ├── create_admin_user.py # Create Django admin user
│   └── start_frontend.py # Start React frontend
├── tests/                 # All test files
│   ├── api/              # Django API tests
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── data/                  # User data
│   ├── input/            # Input PDF files
│   └── output/           # Generated CSV files
├── temp/                  # Runtime temporary files
│   ├── uploads/          # Uploaded PDF files
│   └── outputs/          # Generated output files
├── docs/                  # Documentation
├── config.json           # Configuration file
├── requirements.txt      # Python dependencies
└── README.md
```

## Django Backend API

The Django backend provides a REST API with the following endpoints:

### API Endpoints
- `POST /api/upload/` - Upload PDFs with parser selection
- `POST /api/process/<session_id>/` - Process uploaded files
- `GET /api/status/<session_id>/` - Check processing status
- `GET /api/download/<session_id>/` - Download CSV results
- `DELETE /api/cleanup/<session_id>/` - Clean up session files
- `GET /api/parser-types/` - Get available parser types

### Database Models
- **ProcessingSession**: Tracks file processing sessions
- **UploadedFile**: Individual file records with parser configuration

### Features
- Session-based processing with UUID tracking
- Manual parser selection for each file
- Account holder support (husband/spouse)
- File cleanup and error handling
- Django admin interface for monitoring

## Development Notes

- Each parser inherits from BaseParser and implements `extract_data()`
- Date conversion uses Excel numeric format for compatibility
- OCR fallback handles scanned PDFs when text extraction fails
- Spouse account processing supported via `is_spouse` parameter
- Transaction amounts normalized to positive values in output
- Django backend uses SQLite for development (configurable for production)