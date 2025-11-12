from typing import Type
from .base_parser import BaseParser
from .banco_industrial_checking_parser import BancoIndustrialCheckingParser
from .banco_industrial_credit_parser import BancoIndustrialCreditParser
from .banco_industrial_credit_usd_parser import BancoIndustrialCreditUSDParser
from .bam_credit_parser import BAMCreditParser
from .gyt_credit_parser import GyTCreditParser
from .bi_usd_checking_parser import BIUSDCheckingParser
from .bi_checking_csv_parser import BICheckingCSVParser
from .bi_usd_checking_csv_parser import BIUSDCheckingCSVParser

class ParserFactory:
    @staticmethod
    def get_parser(bank_type: str, account_type: str, pdf_path: str, is_spouse: bool = False):
        """
        Factory method to get the appropriate parser based on bank and account type.
        
        Args:
            bank_type (str): The bank type ('industrial' or 'bam' or 'gyt')
            account_type (str): The account type ('checking' or 'credit' or 'usd_checking')
            pdf_path (str): Path to the PDF file
            is_spouse (bool): Whether this is a spouse's account
            
        Returns:
            BaseParser: An instance of the appropriate parser
        """
        if bank_type == "industrial":
            if account_type == "checking":
                return BancoIndustrialCheckingParser(pdf_path, is_spouse)
            elif account_type == "usd_checking":
                return BIUSDCheckingParser(pdf_path, is_spouse)
            elif account_type == "credit":
                return BancoIndustrialCreditParser(pdf_path, is_spouse)
            elif account_type == "credit_usd":
                return BancoIndustrialCreditUSDParser(pdf_path, is_spouse)
        elif bank_type == "bam" and account_type == "credit":
            return BAMCreditParser(pdf_path)
        elif bank_type == "gyt" and account_type == "credit":
            return GyTCreditParser(pdf_path, is_spouse)

        raise ValueError(f"No parser available for bank_type='{bank_type}' and account_type='{account_type}'")

    @staticmethod
    def get_csv_parser(bank_type: str, account_type: str, csv_path: str, is_spouse: bool = False):
        """
        Factory method to get the appropriate CSV parser based on bank and account type.

        Args:
            bank_type (str): The bank type (currently only 'industrial' supported)
            account_type (str): The account type ('checking' or 'usd_checking')
            csv_path (str): Path to the CSV file
            is_spouse (bool): Whether this is a spouse's account

        Returns:
            BaseParser: An instance of the appropriate CSV parser
        """
        if bank_type == "industrial":
            if account_type == "checking":
                return BICheckingCSVParser(csv_path, is_spouse)
            elif account_type == "usd_checking":
                return BIUSDCheckingCSVParser(csv_path, is_spouse)

        raise ValueError(f"No CSV parser available for bank_type='{bank_type}' and account_type='{account_type}'")