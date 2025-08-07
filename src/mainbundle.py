from parsers.parser_factory import ParserFactory
from datetime import datetime
import os
import pandas as pd

def convert_to_excel_date(date):
    """Convert a date to Excel's numeric format (days since 1900-01-01)"""
    if isinstance(date, datetime.date):
        # Convert to datetime for Excel compatibility
        dt = datetime.combine(date, datetime.min.time())
        # Convert to Excel numeric date (days since 1900-01-01)
        return (dt - datetime(1900, 1, 1)).days + 2  # +2 for Excel's date system
    return date

def get_default_output_name() -> str:
    """Generate default output filename based on current date"""
    date_str = datetime.now().strftime('%Y%m%d')
    return f"all_transactions_{date_str}.xlsx"  # Changed to .xlsx

def get_pdf_files(folder_path: str) -> list:
    """Get all PDF files from the specified folder"""
    pdf_files = []
    try:
        for file in os.listdir(folder_path):
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(folder_path, file)
                pdf_files.append(full_path)
    except Exception as e:
        print(f"Error reading folder: {str(e)}")
    return pdf_files

def get_account_name(bank_type: str, account_type: str) -> str:
    """Get standardized account name based on bank and account type"""
    if bank_type == "industrial":
        if account_type == "checking":
            return "Industrial GTQ"
        elif account_type == "credit":
            return "BI 1116"
        elif account_type == "usd_checking":
            return "Industrial USD 9384"
    elif bank_type == "bam":
        return "BAM 6859"
    elif bank_type == "gyt":
        return "GyT 5978"
    return "Unknown Account"

def create_csv_file(transactions: list, account_name: str):
    """Create a CSV file with standardized columns using account name"""
    # Create safe filename from account name (remove special characters)
    safe_filename = account_name.replace(" ", "_").replace("/", "_")
    output_path = f"{safe_filename}.csv"
    
    # Create DataFrame with required columns
    df = pd.DataFrame({
        'Date': [convert_to_excel_date(t['Date']) for t in transactions],
        'Merchant': [t['Description'] for t in transactions],
        'Category': [t['Category'] for t in transactions],
        'Account': [t['Account Name'] for t in transactions],
        'Original Statement': [t['Original Description'] for t in transactions],
        'Notes': [''] * len(transactions),  # Empty notes column
        'Amount': [abs(t['Amount']) for t in transactions],  # Use abs() to ensure positive amounts
        'Tags': [''] * len(transactions)  # Empty tags column
    })
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Created CSV file: {output_path}")
    return output_path

def main():
    # Get folder path from user
    folder_path = input("Enter the folder path containing your PDF files: ").strip()
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return
    
    # Get all PDF files from the folder
    pdf_paths = get_pdf_files(folder_path)
    
    if not pdf_paths:
        print("No PDF files found in the specified folder.")
        return
    
    print(f"\nFound {len(pdf_paths)} PDF files to process:")
    for i, path in enumerate(pdf_paths, 1):
        print(f"{i}. {os.path.basename(path)}")
    
    # Create a dictionary to store parser type for each file
    file_parsers = {}
    
    # Get parser type for each file
    print("\nFor each file, select the appropriate parser.")
    for pdf_path in pdf_paths:
        print(f"\nSelect parser for: {os.path.basename(pdf_path)}")
        print("1. Banco Industrial - Checking Account")
        print("2. Banco Industrial - Credit Card")
        print("3. BAM - Credit Card")
        print("4. GyT - Credit Card")
        print("5. Banco Industrial - USD Checking Account")
        
        while True:
            choice = input("\nEnter your choice (1-5): ")
            if choice == "1":
                bank_type = "industrial"
                account_type = "checking"
                break
            elif choice == "2":
                bank_type = "industrial"
                account_type = "credit"
                break
            elif choice == "3":
                bank_type = "bam"
                account_type = "credit"
                break
            elif choice == "4":
                bank_type = "gyt"
                account_type = "credit"
                break
            elif choice == "5":
                bank_type = "industrial"
                account_type = "usd_checking"
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        
        file_parsers[pdf_path] = (bank_type, account_type)
    
    try:
        # Generate default output filename for Excel
        default_output = get_default_output_name()
        output_file = input(f"\nEnter name for output Excel file (default: {default_output}): ") or default_output
        if not output_file.endswith('.xlsx'):
            output_file += '.xlsx'
        
        # Process all PDFs and store transactions by file
        transactions_by_file = {}
        all_transactions = []
        created_csv_files = set()  # Track created CSV files
        
        for pdf_path in pdf_paths:
            bank_type, account_type = file_parsers[pdf_path]
            print(f"\nProcessing: {os.path.basename(pdf_path)}")
            print(f"Using parser: {bank_type} - {account_type}")
            
            try:
                # Create parser for each PDF
                parser = ParserFactory.get_parser(
                    bank_type=bank_type,
                    account_type=account_type,
                    pdf_path=pdf_path
                )
                
                print(f"Parser created successfully. Extracting data...")
                
                # Extract transactions
                transactions = parser.extract_data()
                
                if not transactions:
                    print(f"Warning: No transactions found in {os.path.basename(pdf_path)}")
                    continue
                
                print(f"Found {len(transactions)} transactions")
                
                # Update account name for all transactions
                account_name = get_account_name(bank_type, account_type)
                for transaction in transactions:
                    transaction['Account Name'] = account_name
                
                # Sort transactions by date
                transactions.sort(key=lambda x: x['Date'])
                
                # Store transactions with a sheet name based on the file
                sheet_name = os.path.splitext(os.path.basename(pdf_path))[0][:31]
                transactions_by_file[sheet_name] = transactions
                
                # Add to all transactions list
                all_transactions.extend(transactions)
                
                # Create or append to CSV file for this account
                csv_path = create_csv_file(transactions, account_name)
                created_csv_files.add(csv_path)
                
                print(f"Successfully processed {len(transactions)} transactions in {os.path.basename(pdf_path)}")
                
            except Exception as e:
                print(f"Error processing {os.path.basename(pdf_path)}: {str(e)}")
                print("Continuing with next file...")
                continue
        
        if not transactions_by_file:
            print("\nNo transactions were found in any of the PDF files.")
            print("Please check that:")
            print("1. The PDF files are not empty")
            print("2. The correct parser was selected for each file")
            print("3. The PDF files are in the expected format")
            return
            
        # Sort all transactions by date and account name
        all_transactions.sort(key=lambda x: (x['Date'], x['Account Name']))
            
        try:
            # Write all transactions to Excel file with multiple sheets
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # First, write the summary sheet with all transactions
                df_all = pd.DataFrame(all_transactions)
                
                if df_all.empty:
                    print("\nError: No transactions were found to write to Excel.")
                    return
                
                # Convert dates to Excel numeric format
                df_all['Date'] = df_all['Date'].apply(convert_to_excel_date)
                
                # Set column order for All Transactions sheet
                summary_columns_order = [
                    'Date',
                    'Description',
                    'Original Description',
                    'Amount',
                    'Transaction Type',
                    'Category',
                    'Account Name',
                    'Labels',  # Add Labels column
                    'Notes'    # Add Notes column
                ]
                
                # Apply column order to All Transactions sheet and ensure positive amounts
                df_all = df_all[summary_columns_order]
                df_all['Amount'] = df_all['Amount'].abs()  # Ensure all amounts are positive
                # Initialize empty Labels and Notes columns
                df_all['Labels'] = ''
                df_all['Notes'] = ''
                df_all.to_excel(writer, sheet_name='All Transactions', index=False)
                print(f"\nAdded {len(all_transactions)} transactions to sheet: All Transactions")
                
                # Then write individual sheets with available columns
                for sheet_name, transactions in transactions_by_file.items():
                    df = pd.DataFrame(transactions)
                    if not df.empty:
                        # Get available columns for this sheet
                        available_columns = df.columns.tolist()
                        # Use the same order as summary sheet
                        columns_to_use = summary_columns_order.copy()
                        
                        # Add Original Value and Currency if they exist
                        if 'Original Value' in available_columns:
                            columns_to_use.append('Original Value')
                        if 'Original Currency' in available_columns:
                            columns_to_use.append('Original Currency')
                        
                        # Convert dates to Excel numeric format
                        df['Date'] = df['Date'].apply(convert_to_excel_date)
                        
                        df = df[columns_to_use]
                        df['Amount'] = df['Amount'].abs()  # Ensure all amounts are positive
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"Added {len(transactions)} transactions to sheet: {sheet_name}")
            
            print(f"\nSuccess! Files created:")
            print(f"- Excel file: {output_file}")
            print("- CSV files:")
            for csv_file in sorted(created_csv_files):
                print(f"  - {csv_file}")
                
        except Exception as e:
            print(f"\nAn error occurred while creating the Excel file: {str(e)}")
            if "At least one sheet must be visible" in str(e):
                print("\nNo transactions were found to write to Excel. Please check that:")
                print("1. The PDF files contain valid transaction data")
                print("2. The correct parser was selected for each file")
                print("3. The PDF files are in the expected format")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 