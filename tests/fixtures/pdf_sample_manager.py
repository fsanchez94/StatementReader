"""
PDF Sample Management Utilities

This module provides utilities for managing sample PDF files used in testing.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from src.parsers.parser_factory import ParserFactory
from test_data_loader import (
    get_sample_pdfs_by_type, 
    get_expected_output_for_pdf,
    get_expected_outputs_dir,
    validate_sample_pdf_structure
)


class PDFSampleManager:
    """Manager for PDF sample files and their expected outputs"""
    
    def __init__(self):
        self.temp_dir = None
    
    def generate_expected_output(self, pdf_path: str, bank_type: str, account_type: str, 
                               is_spouse: bool = False) -> str:
        """Generate expected CSV output for a PDF sample
        
        Args:
            pdf_path (str): Path to the PDF file
            bank_type (str): Bank type
            account_type (str): Account type  
            is_spouse (bool): Whether this is a spouse account
            
        Returns:
            str: Path to generated CSV file
        """
        # Get parser for this PDF
        parser = ParserFactory.get_parser(bank_type, account_type, pdf_path, is_spouse=is_spouse)
        
        # Extract data
        transactions = parser.extract_data()
        
        # Generate output filename
        pdf_name = Path(pdf_path).stem
        if is_spouse:
            pdf_name += "_spouse"
            
        expected_outputs_dir = get_expected_outputs_dir() / bank_type
        expected_outputs_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = expected_outputs_dir / f"{pdf_name}.csv"
        
        # Save to CSV
        parser.to_csv(str(output_path))
        
        print(f"Generated expected output: {output_path}")
        print(f"Transactions found: {len(transactions)}")
        
        return str(output_path)
    
    def generate_all_expected_outputs(self) -> Dict[str, List[str]]:
        """Generate expected outputs for all available sample PDFs
        
        Returns:
            dict: Results summary with generated files by bank type
        """
        results = {}
        
        # Get all available PDF combinations
        from test_data_loader import get_all_sample_pdf_combinations
        combinations = get_all_sample_pdf_combinations()
        
        for bank_type, account_type, pdf_files in combinations:
            if bank_type not in results:
                results[bank_type] = []
                
            for pdf_path in pdf_files:
                try:
                    # Generate for regular account
                    output_path = self.generate_expected_output(
                        pdf_path, bank_type, account_type, is_spouse=False
                    )
                    results[bank_type].append(output_path)
                    
                    # Generate for spouse account if applicable
                    if account_type in ['checking', 'usd_checking']:
                        spouse_output = self.generate_expected_output(
                            pdf_path, bank_type, account_type, is_spouse=True
                        )
                        results[bank_type].append(spouse_output)
                        
                except Exception as e:
                    print(f"Error processing {pdf_path}: {e}")
                    
        return results
    
    def validate_pdf_outputs(self, pdf_path: str, bank_type: str, account_type: str) -> bool:
        """Validate that a PDF produces the expected output
        
        Args:
            pdf_path (str): Path to PDF file
            bank_type (str): Bank type
            account_type (str): Account type
            
        Returns:
            bool: True if output matches expected
        """
        expected_csv = get_expected_output_for_pdf(pdf_path)
        if not expected_csv:
            print(f"No expected output found for {pdf_path}")
            return False
        
        # Generate temporary output
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            temp_output = tmp.name
        
        try:
            parser = ParserFactory.get_parser(bank_type, account_type, pdf_path)
            parser.to_csv(temp_output)
            
            # Compare files (basic check - could be enhanced)
            import pandas as pd
            
            expected_df = pd.read_csv(expected_csv)
            actual_df = pd.read_csv(temp_output)
            
            # Check column names
            if list(expected_df.columns) != list(actual_df.columns):
                print(f"Column mismatch for {pdf_path}")
                return False
            
            # Check row count
            if len(expected_df) != len(actual_df):
                print(f"Row count mismatch for {pdf_path}: expected {len(expected_df)}, got {len(actual_df)}")
                return False
            
            # Check data types and basic content
            for col in expected_df.columns:
                if expected_df[col].dtype != actual_df[col].dtype:
                    print(f"Data type mismatch in column {col} for {pdf_path}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating {pdf_path}: {e}")
            return False
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_output)
            except:
                pass
    
    def report_status(self) -> Dict:
        """Generate a status report of sample PDFs and expected outputs
        
        Returns:
            dict: Status report
        """
        structure_validation = validate_sample_pdf_structure()
        
        report = {
            'structure_valid': structure_validation['valid'],
            'structure_issues': structure_validation['issues'],
            'pdf_summary': structure_validation['summary'],
            'expected_outputs': {},
            'missing_outputs': []
        }
        
        # Check expected outputs
        from test_data_loader import get_all_sample_pdf_combinations
        combinations = get_all_sample_pdf_combinations()
        
        for bank_type, account_type, pdf_files in combinations:
            if bank_type not in report['expected_outputs']:
                report['expected_outputs'][bank_type] = {}
            if account_type not in report['expected_outputs'][bank_type]:
                report['expected_outputs'][bank_type][account_type] = []
                
            for pdf_path in pdf_files:
                expected_csv = get_expected_output_for_pdf(pdf_path)
                pdf_name = Path(pdf_path).name
                
                if expected_csv:
                    report['expected_outputs'][bank_type][account_type].append(pdf_name)
                else:
                    report['missing_outputs'].append(f"{bank_type}/{account_type}/{pdf_name}")
        
        return report


def main():
    """Command line interface for PDF sample management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage PDF samples for testing")
    parser.add_argument('command', choices=['validate', 'generate', 'report'], 
                       help="Command to execute")
    parser.add_argument('--bank', help="Bank type (for generate command)")
    parser.add_argument('--account', help="Account type (for generate command)")
    parser.add_argument('--pdf', help="Specific PDF file (for generate command)")
    
    args = parser.parse_args()
    
    manager = PDFSampleManager()
    
    if args.command == 'report':
        report = manager.report_status()
        print("\n=== PDF Sample Status Report ===")
        print(f"Structure Valid: {report['structure_valid']}")
        
        if report['structure_issues']:
            print("\nStructure Issues:")
            for issue in report['structure_issues']:
                print(f"  - {issue}")
        
        print("\nPDF Summary:")
        for bank, accounts in report['pdf_summary'].items():
            print(f"  {bank}:")
            for account, count in accounts.items():
                print(f"    {account}: {count} PDFs")
        
        if report['missing_outputs']:
            print(f"\nMissing Expected Outputs ({len(report['missing_outputs'])}):")
            for missing in report['missing_outputs']:
                print(f"  - {missing}")
    
    elif args.command == 'generate':
        if args.pdf and args.bank and args.account:
            manager.generate_expected_output(args.pdf, args.bank, args.account)
        else:
            print("Generating all expected outputs...")
            results = manager.generate_all_expected_outputs()
            print(f"Generated outputs for {len(results)} bank types")
    
    elif args.command == 'validate':
        from test_data_loader import get_all_sample_pdf_combinations
        combinations = get_all_sample_pdf_combinations()
        
        total_validated = 0
        total_passed = 0
        
        for bank_type, account_type, pdf_files in combinations:
            for pdf_path in pdf_files:
                total_validated += 1
                if manager.validate_pdf_outputs(pdf_path, bank_type, account_type):
                    total_passed += 1
                    print(f"✓ {Path(pdf_path).name}")
                else:
                    print(f"✗ {Path(pdf_path).name}")
        
        print(f"\nValidation Results: {total_passed}/{total_validated} passed")


if __name__ == "__main__":
    main()