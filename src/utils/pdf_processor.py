import pdfplumber
import pytesseract
from PIL import Image
import io

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PDFProcessor:
    def __init__(self):
        self.ocr_config = '--psm 6'
        
    def process(self, pdf_path: str) -> str:
        try:
            # First try as searchable PDF
            text = self._extract_text(pdf_path)
            if self._is_valid_text(text):
                return text
                
            # If text extraction fails, try OCR
            return self._process_with_ocr(pdf_path)
        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def _extract_text(self, pdf_path: str) -> str:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text.append(page.extract_text() or '')
        return '\n'.join(full_text)
    
    def _process_with_ocr(self, pdf_path: str) -> str:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                img = page.to_image()
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                pil_image = Image.open(img_bytes)
                text = pytesseract.image_to_string(pil_image, config=self.ocr_config)
                full_text.append(text)
        return '\n'.join(full_text)
    
    def _is_valid_text(self, text: str) -> bool:
        return bool(text and len(text.strip()) >= 50)