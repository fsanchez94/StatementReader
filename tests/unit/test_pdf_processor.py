import pytest
from unittest.mock import Mock, patch, MagicMock
from src.utils.pdf_processor import PDFProcessor
import pdfplumber
from PIL import Image
import io

class TestPDFProcessor:
    def test_init(self):
        """Test PDFProcessor initialization"""
        processor = PDFProcessor()
        assert processor.ocr_config == '--psm 6'

    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_extract_text_success(self, mock_pdfplumber):
        """Test successful text extraction from PDF"""
        # Setup mock PDF with pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor._extract_text("test.pdf")
        
        assert result == "Page 1 content\nPage 2 content"
        mock_pdfplumber.assert_called_once_with("test.pdf")

    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_extract_text_with_none_content(self, mock_pdfplumber):
        """Test text extraction when page returns None"""
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        processor = PDFProcessor()
        result = processor._extract_text("test.pdf")
        
        assert result == ""

    def test_is_valid_text(self):
        """Test text validation logic"""
        processor = PDFProcessor()
        
        # Valid text (>= 50 characters)
        valid_text = "This is a valid text that has more than fifty characters in it"
        assert processor._is_valid_text(valid_text) is True
        
        # Invalid text (< 50 characters)
        invalid_text = "Too short"
        assert processor._is_valid_text(invalid_text) is False
        
        # Empty text
        assert processor._is_valid_text("") is False
        assert processor._is_valid_text(None) is False
        
        # Whitespace only
        assert processor._is_valid_text("   \n\t   ") is False

    @patch('src.utils.pdf_processor.pytesseract.image_to_string')
    @patch('src.utils.pdf_processor.Image.open')
    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_process_with_ocr(self, mock_pdfplumber, mock_image_open, mock_tesseract):
        """Test OCR processing"""
        # Setup mock PDF page
        mock_img = Mock()
        mock_img.save = Mock()
        
        mock_page = Mock()
        mock_page.to_image.return_value = mock_img
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Setup PIL Image mock
        mock_pil_image = Mock(spec=Image.Image)
        mock_image_open.return_value = mock_pil_image
        
        # Setup Tesseract mock
        mock_tesseract.return_value = "OCR extracted text"
        
        processor = PDFProcessor()
        result = processor._process_with_ocr("test.pdf")
        
        assert result == "OCR extracted text"
        mock_tesseract.assert_called_once_with(mock_pil_image, config='--psm 6')

    @patch('src.utils.pdf_processor.PDFProcessor._process_with_ocr')
    @patch('src.utils.pdf_processor.PDFProcessor._extract_text')
    def test_process_fallback_to_ocr(self, mock_extract, mock_ocr):
        """Test that process falls back to OCR when text extraction fails validation"""
        # First extraction returns invalid text
        mock_extract.return_value = "short"
        mock_ocr.return_value = "This is a long OCR result that should be valid and contain enough text"
        
        processor = PDFProcessor()
        result = processor.process("test.pdf")
        
        assert result == "This is a long OCR result that should be valid and contain enough text"
        mock_extract.assert_called_once()
        mock_ocr.assert_called_once()

    @patch('src.utils.pdf_processor.PDFProcessor._extract_text')
    def test_process_success_with_valid_text(self, mock_extract):
        """Test that process returns extracted text when it's valid"""
        valid_text = "This is valid extracted text that is long enough to pass validation"
        mock_extract.return_value = valid_text
        
        processor = PDFProcessor()
        result = processor.process("test.pdf")
        
        assert result == valid_text
        mock_extract.assert_called_once()

    @patch('src.utils.pdf_processor.PDFProcessor._extract_text')
    def test_process_exception_handling(self, mock_extract):
        """Test exception handling in process method"""
        mock_extract.side_effect = Exception("PDF processing error")
        
        processor = PDFProcessor()
        
        with pytest.raises(Exception) as exc_info:
            processor.process("test.pdf")
        
        assert "Failed to process PDF: PDF processing error" in str(exc_info.value)

    @patch('src.utils.pdf_processor.pytesseract.image_to_string')
    @patch('src.utils.pdf_processor.Image.open')
    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_process_with_ocr_multiple_pages(self, mock_pdfplumber, mock_image_open, mock_tesseract):
        """Test OCR processing with multiple pages"""
        # Setup mock PDF with multiple pages
        mock_img1 = Mock()
        mock_img1.save = Mock()
        mock_page1 = Mock()
        mock_page1.to_image.return_value = mock_img1
        
        mock_img2 = Mock()
        mock_img2.save = Mock()
        mock_page2 = Mock()
        mock_page2.to_image.return_value = mock_img2
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Setup PIL Image mock
        mock_pil_image = Mock(spec=Image.Image)
        mock_image_open.return_value = mock_pil_image
        
        # Setup Tesseract mock to return different text for each page
        mock_tesseract.side_effect = ["OCR page 1 text", "OCR page 2 text"]
        
        processor = PDFProcessor()
        result = processor._process_with_ocr("test.pdf")
        
        assert result == "OCR page 1 text\nOCR page 2 text"
        assert mock_tesseract.call_count == 2

    @patch('src.utils.pdf_processor.pytesseract.image_to_string')
    @patch('src.utils.pdf_processor.pdfplumber.open')
    def test_process_with_ocr_exception(self, mock_pdfplumber, mock_tesseract):
        """Test OCR processing when Tesseract fails"""
        # Setup mock PDF page
        mock_img = Mock()
        mock_img.save = Mock()
        
        mock_page = Mock()
        mock_page.to_image.return_value = mock_img
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Make Tesseract throw an exception
        mock_tesseract.side_effect = Exception("OCR failed")
        
        processor = PDFProcessor()
        
        with pytest.raises(Exception):
            processor._process_with_ocr("test.pdf")