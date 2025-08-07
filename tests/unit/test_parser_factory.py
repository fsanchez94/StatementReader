import pytest
from parsers.parser_factory import ParserFactory
from parsers.banco_industrial_checking_parser import BancoIndustrialCheckingParser
from parsers.banco_industrial_credit_parser import BancoIndustrialCreditParser
from parsers.banco_industrial_credit_usd_parser import BancoIndustrialCreditUSDParser
from parsers.bi_usd_checking_parser import BIUSDCheckingParser
from parsers.bam_credit_parser import BAMCreditParser
from parsers.gyt_credit_parser import GyTCreditParser

class TestParserFactory:
    def test_get_parser_industrial_checking(self):
        """Test factory returns correct parser for Industrial checking account"""
        parser = ParserFactory.get_parser("industrial", "checking", "test.pdf")
        assert isinstance(parser, BancoIndustrialCheckingParser)
        assert parser.pdf_path == "test.pdf"
        assert parser.is_spouse is False

    def test_get_parser_industrial_checking_spouse(self):
        """Test factory returns correct parser for Industrial checking account (spouse)"""
        parser = ParserFactory.get_parser("industrial", "checking", "test.pdf", is_spouse=True)
        assert isinstance(parser, BancoIndustrialCheckingParser)
        assert parser.is_spouse is True

    def test_get_parser_industrial_usd_checking(self):
        """Test factory returns correct parser for Industrial USD checking account"""
        parser = ParserFactory.get_parser("industrial", "usd_checking", "test.pdf")
        assert isinstance(parser, BIUSDCheckingParser)
        assert parser.pdf_path == "test.pdf"

    def test_get_parser_industrial_credit(self):
        """Test factory returns correct parser for Industrial credit card"""
        parser = ParserFactory.get_parser("industrial", "credit", "test.pdf")
        assert isinstance(parser, BancoIndustrialCreditParser)
        assert parser.pdf_path == "test.pdf"

    def test_get_parser_industrial_credit_usd(self):
        """Test factory returns correct parser for Industrial USD credit card"""
        parser = ParserFactory.get_parser("industrial", "credit_usd", "test.pdf")
        assert isinstance(parser, BancoIndustrialCreditUSDParser)
        assert parser.pdf_path == "test.pdf"

    def test_get_parser_bam_credit(self):
        """Test factory returns correct parser for BAM credit card"""
        parser = ParserFactory.get_parser("bam", "credit", "test.pdf")
        assert isinstance(parser, BAMCreditParser)
        assert parser.pdf_path == "test.pdf"

    def test_get_parser_gyt_credit(self):
        """Test factory returns correct parser for GyT credit card"""
        parser = ParserFactory.get_parser("gyt", "credit", "test.pdf")
        assert isinstance(parser, GyTCreditParser)
        assert parser.pdf_path == "test.pdf"

    def test_get_parser_gyt_credit_spouse(self):
        """Test factory returns correct parser for GyT credit card (spouse)"""
        parser = ParserFactory.get_parser("gyt", "credit", "test.pdf", is_spouse=True)
        assert isinstance(parser, GyTCreditParser)
        assert parser.is_spouse is True

    def test_get_parser_invalid_bank_type(self):
        """Test factory raises ValueError for invalid bank type"""
        with pytest.raises(ValueError) as exc_info:
            ParserFactory.get_parser("invalid_bank", "checking", "test.pdf")
        
        assert "No parser available for bank_type='invalid_bank' and account_type='checking'" in str(exc_info.value)

    def test_get_parser_invalid_account_type(self):
        """Test factory raises ValueError for invalid account type"""
        with pytest.raises(ValueError) as exc_info:
            ParserFactory.get_parser("industrial", "invalid_account", "test.pdf")
        
        assert "No parser available for bank_type='industrial' and account_type='invalid_account'" in str(exc_info.value)

    def test_get_parser_unsupported_combination(self):
        """Test factory raises ValueError for unsupported bank/account combinations"""
        # BAM only supports credit accounts
        with pytest.raises(ValueError) as exc_info:
            ParserFactory.get_parser("bam", "checking", "test.pdf")
        
        assert "No parser available for bank_type='bam' and account_type='checking'" in str(exc_info.value)

        # GyT only supports credit accounts
        with pytest.raises(ValueError) as exc_info:
            ParserFactory.get_parser("gyt", "checking", "test.pdf")
        
        assert "No parser available for bank_type='gyt' and account_type='checking'" in str(exc_info.value)

    def test_get_parser_case_sensitivity(self):
        """Test that factory is case sensitive for bank and account types"""
        # Test uppercase bank type
        with pytest.raises(ValueError):
            ParserFactory.get_parser("INDUSTRIAL", "checking", "test.pdf")
        
        # Test uppercase account type
        with pytest.raises(ValueError):
            ParserFactory.get_parser("industrial", "CHECKING", "test.pdf")

    def test_get_parser_all_supported_combinations(self):
        """Test all supported bank/account combinations"""
        supported_combinations = [
            ("industrial", "checking", BancoIndustrialCheckingParser),
            ("industrial", "usd_checking", BIUSDCheckingParser),
            ("industrial", "credit", BancoIndustrialCreditParser),
            ("industrial", "credit_usd", BancoIndustrialCreditUSDParser),
            ("bam", "credit", BAMCreditParser),
            ("gyt", "credit", GyTCreditParser),
        ]
        
        for bank_type, account_type, expected_class in supported_combinations:
            parser = ParserFactory.get_parser(bank_type, account_type, "test.pdf")
            assert isinstance(parser, expected_class)
            assert parser.pdf_path == "test.pdf"

    def test_get_parser_with_special_characters_in_path(self):
        """Test factory with special characters in PDF path"""
        special_path = "C:\\Users\\Test User\\Documents\\My File (2024).pdf"
        parser = ParserFactory.get_parser("industrial", "checking", special_path)
        assert parser.pdf_path == special_path

    def test_get_parser_with_empty_path(self):
        """Test factory with empty PDF path"""
        parser = ParserFactory.get_parser("industrial", "checking", "")
        assert parser.pdf_path == ""

    def test_get_parser_none_values(self):
        """Test factory behavior with None values"""
        with pytest.raises(ValueError):
            ParserFactory.get_parser(None, "checking", "test.pdf")
        
        with pytest.raises(ValueError):
            ParserFactory.get_parser("industrial", None, "test.pdf")