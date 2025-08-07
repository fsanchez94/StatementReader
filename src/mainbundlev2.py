from parsers.parser_factory import ParserFactory
from datetime import datetime, date
import os
import pandas as pd
import json

def convert_to_excel_date(date_value):
    """Convert a date to Excel's numeric format (days since 1900-01-01)"""
    if isinstance(date_value, date):
        # Convert to datetime for Excel compatibility
        dt = datetime.combine(date_value, datetime.min.time())
        # Convert to Excel numeric date (days since 1900-01-01)
        return (dt - datetime(1900, 1, 1)).days + 2  # +2 for Excel's date system
    return date_value

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

def create_csv_file(transactions: list, account_name: str, output_path: str):
    """Create a CSV file with standardized columns using account name"""
    # Create DataFrame with required columns
    df = pd.DataFrame({
        'Date': [t['Date'] for t in transactions],
        'Description': [t['Description'] for t in transactions],
        'Original Description': [t['Original Description'] for t in transactions],
        'Amount': [abs(t['Amount']) for t in transactions],
        'Transaction Type': [t['Transaction Type'] for t in transactions],
        'Category': [t['Category'] for t in transactions],
        'Account Name': [t['Account Name'] for t in transactions]
    })
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Created CSV file: {output_path}")

def create_combined_csv(transactions: list, output_path: str):
    """Create a combined CSV file with all transactions"""
    # Create DataFrame with all required columns
    df = pd.DataFrame({
        'Date': [convert_to_excel_date(t['Date']) for t in transactions],
        'Description': [t['Description'] for t in transactions],
        'Original Description': [t['Original Description'] for t in transactions],
        'Amount': [abs(t['Amount']) for t in transactions],
        'Transaction Type': [t['Transaction Type'] for t in transactions],
        'Category': [t['Category'] for t in transactions],
        'Account Name': [t['Account Name'] for t in transactions],
        'Labels': [''] * len(transactions),  # Empty Labels column
        'Notes': [''] * len(transactions)    # Empty Notes column
    })
    
    # Sort by date and account name
    df = df.sort_values(['Date', 'Account Name'])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nCreated combined CSV file: {output_path}")

def load_config():
    """Load configuration from config.json file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        print("Please create a config.json file with the folder paths.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file {config_path}")
        return None

def main():
    # Load paths from config file
    config = load_config()
    if config is None:
        return
    
    husband_path = config['paths']['husband_folder']
    spouse_path = config['paths']['spouse_folder']
    output_path = config['paths']['output_folder']
    
    print(f"\nUsing paths from config.json:")
    print(f"Husband's folder: {husband_path}")
    print(f"Spouse's folder: {spouse_path}")
    print(f"Output folder: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Validate paths
    if not os.path.exists(husband_path):
        print(f"Error: Husband's folder not found: {husband_path}")
        return
    if not os.path.exists(spouse_path):
        print(f"Error: Spouse's folder not found: {spouse_path}")
        return
    
    # Get all PDF files from both folders
    husband_pdfs = get_pdf_files(husband_path)
    spouse_pdfs = get_pdf_files(spouse_path)
    
    if not husband_pdfs and not spouse_pdfs:
        print("No PDF files found in either folder.")
        return
    
    # Create a dictionary to store parser type for each file
    file_parsers = {}
    
    # Process husband's files
    if husband_pdfs:
        print(f"\nFound {len(husband_pdfs)} PDF files in husband's folder:")
        for i, path in enumerate(husband_pdfs, 1):
            print(f"{i}. {os.path.basename(path)}")
        
        print("\nFor each husband's file, select the appropriate parser.")
        for pdf_path in husband_pdfs:
            print(f"\nSelect parser for: {os.path.basename(pdf_path)}")
            print("1. Bi Checking GTQ")
            print("2. BI Checking USD")
            print("3. BI Credit GTQ")
            print("4. BI Credit USD")
            print("5. GyT Credit")
            
            while True:
                choice = input("\nEnter your choice (1-5): ")
                if choice == "1":
                    bank_type = "industrial"
                    account_type = "checking"
                    break
                elif choice == "2":
                    bank_type = "industrial"
                    account_type = "usd_checking"
                    break
                elif choice == "3":
                    bank_type = "industrial"
                    account_type = "credit"
                    break
                elif choice == "4":
                    bank_type = "industrial"
                    account_type = "credit_usd"
                    break
                elif choice == "5":
                    bank_type = "gyt"
                    account_type = "credit"
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")
            
            file_parsers[pdf_path] = (bank_type, account_type, False)  # False for husband
    
    # Process spouse's files
    if spouse_pdfs:
        print(f"\nFound {len(spouse_pdfs)} PDF files in spouse's folder:")
        for i, path in enumerate(spouse_pdfs, 1):
            print(f"{i}. {os.path.basename(path)}")
        
        print("\nFor each spouse's file, select the appropriate parser.")
        for pdf_path in spouse_pdfs:
            print(f"\nSelect parser for: {os.path.basename(pdf_path)}")
            print("1. Bi Checking GTQ")
            print("2. BI Checking USD")
            print("3. BI Credit GTQ")
            print("4. BI Credit USD")
            print("5. GyT Credit")
            
            while True:
                choice = input("\nEnter your choice (1-5): ")
                if choice == "1":
                    bank_type = "industrial"
                    account_type = "checking"
                    break
                elif choice == "2":
                    bank_type = "industrial"
                    account_type = "usd_checking"
                    break
                elif choice == "3":
                    bank_type = "industrial"
                    account_type = "credit"
                    break
                elif choice == "4":
                    bank_type = "industrial"
                    account_type = "credit_usd"
                    break
                elif choice == "5":
                    bank_type = "gyt"
                    account_type = "credit"
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")
            
            file_parsers[pdf_path] = (bank_type, account_type, True)  # True for spouse
    
    try:
        # List to store all transactions
        all_transactions = []
        
        # Process each PDF and create CSV files
        for pdf_path in list(file_parsers.keys()):
            bank_type, account_type, is_spouse = file_parsers[pdf_path]
            print(f"\nProcessing: {os.path.basename(pdf_path)}")
            print(f"Using parser: {bank_type} - {account_type}")
            print(f"Account holder: {'Spouse' if is_spouse else 'Husband'}")
            
            # Get document name without extension
            document_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            try:
                # Create parser for the PDF
                parser = ParserFactory.get_parser(
                    bank_type=bank_type,
                    account_type=account_type,
                    pdf_path=pdf_path,
                    is_spouse=is_spouse
                )
                
                print(f"Parser created successfully. Extracting data...")
                
                # Extract transactions
                transactions = parser.extract_data()
                
                if not transactions:
                    print(f"Warning: No transactions found in {os.path.basename(pdf_path)}")
                    continue
                
                print(f"Found {len(transactions)} transactions")
                
                # Set Account Name to document name for each transaction
                for t in transactions:
                    t['Account Name'] = document_name
                
                # Sort transactions by date
                transactions.sort(key=lambda x: x['Date'])
                
                # Create CSV file for this PDF
                output_filename = os.path.join(output_path, f"{document_name}.csv")
                create_csv_file(transactions, document_name, output_filename)
                
                # Add transactions to the combined list
                all_transactions.extend(transactions)
                
                print(f"Successfully processed {len(transactions)} transactions in {os.path.basename(pdf_path)}")
                
            except Exception as e:
                print(f"Error processing {os.path.basename(pdf_path)}: {str(e)}")
                print("Continuing with next file...")
                continue
        
        # Create combined CSV file if we have transactions
        if all_transactions:
            # Generate default output filename based on current date
            date_str = datetime.now().strftime('%Y%m%d')
            combined_filename = os.path.join(output_path, f"all_transactions_{date_str}.csv")
            create_combined_csv(all_transactions, combined_filename)
        else:
            print("\nNo transactions were found in any of the PDF files.")
            print("Please check that:")
            print("1. The PDF files are not empty")
            print("2. The correct parser was selected for each file")
            print("3. The PDF files are in the expected format")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 