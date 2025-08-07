from parsers.parser_factory import ParserFactory
from datetime import datetime

def get_default_output_name(bank_type: str, account_type: str) -> str:
    """Generate default output filename based on parser type and current date"""
    date_str = datetime.now().strftime('%Y%m%d')
    
    if bank_type == "industrial":
        prefix = "bi"  # Banco Industrial
    elif bank_type == "bam":
        prefix = "bam"
    elif bank_type == "gyt":
        prefix = "gyt"
    else:
        prefix = "bank"
        
    return f"{prefix}_{account_type}_{date_str}.csv"

def main():
    # Get PDF path from user
    pdf_path = input("Please enter the path to your PDF file: ")
    
    # Get bank and account type from user
    print("\nSelect bank and account type:")
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
    
    try:
        # Create parser
        parser = ParserFactory.get_parser(
            bank_type=bank_type,
            account_type=account_type,
            pdf_path=pdf_path
        )
        
        # Generate default output filename
        default_output = get_default_output_name(bank_type, account_type)
        
        # Get output filename from user, using the generated default
        output_file = input(f"\nEnter name for output CSV file (default: {default_output}): ") or default_output
        if not output_file.endswith('.csv'):
            output_file += '.csv'
            
        # Convert to CSV
        parser.to_csv(output_file)
        print(f"\nSuccess! Transactions have been saved to {output_file}")
        
    except FileNotFoundError:
        print(f"\nError: Could not find the PDF file at: {pdf_path}")
        print("Please make sure the file path is correct and try again.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()