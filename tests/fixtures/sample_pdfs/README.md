# Sample PDFs for Testing

This directory contains real bank statement PDF examples used for testing the parsers.

## Directory Structure

```
sample_pdfs/
├── industrial/           # Banco Industrial PDFs
│   ├── checking/        # GTQ checking account statements
│   ├── usd_checking/    # USD checking account statements  
│   ├── credit/          # Credit card statements
│   └── credit_usd/      # USD credit card statements
├── bam/                 # BAM bank PDFs
│   └── credit/          # BAM credit card statements
└── gyt/                 # GyT bank PDFs
    └── credit/          # GyT credit card statements
```

## Adding Sample PDFs

To add new sample PDFs for testing:

1. **Place PDF in appropriate directory** based on bank and account type
2. **Use descriptive filenames** like `industrial_checking_jan2024.pdf`
3. **Anonymize sensitive data** - ensure no real account numbers, names, or personal information
4. **Generate expected output** by running the parser and verifying the CSV output
5. **Place expected CSV** in `../expected_outputs/{bank}/` with matching filename

## File Naming Convention

- `{bank}_{account_type}_{description}.pdf`
- Examples:
  - `industrial_checking_sample1.pdf`
  - `bam_credit_example.pdf`
  - `gyt_credit_multipage.pdf`

## Security Note

⚠️ **IMPORTANT**: Never commit PDFs containing real personal or financial information. 
All sample PDFs should be anonymized or use fictional data only.