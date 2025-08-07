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

Run single PDF processing (interactive):
```bash
python src/main.py
```

Run batch processing (multiple PDFs, interactive) - **PRIMARY SCRIPT**:
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

Run alternative batch processing:
```bash
python src/mainbundle.py
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
├── src/                     # Source code only
│   ├── main.py             # Single PDF processor
│   ├── mainbundle.py       # Batch processor (Excel output)
│   ├── mainbundlev2.py     # Primary batch processor (CSV output)
│   ├── parsers/            # Bank-specific parsers
│   └── utils/              # Shared utilities
├── data/
│   ├── input/
│   │   ├── husband/        # Husband's PDF statements
│   │   └── spouse/         # Spouse's PDF statements
│   └── output/
│       └── csv/            # Generated CSV files
├── config.json             # Configuration file for folder paths
├── requirements.txt
├── README.md
└── CLAUDE.md
```

## Development Notes

- Each parser inherits from BaseParser and implements `extract_data()`
- Date conversion uses Excel numeric format for compatibility
- OCR fallback handles scanned PDFs when text extraction fails
- Spouse account processing supported via `is_spouse` parameter
- Transaction amounts normalized to positive values in output