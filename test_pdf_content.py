#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.pdf_processor import PDFProcessor

def test_pdf_content():
    pdf_files = list(Path("data/input/husband").glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found")
        return
    
    test_file = pdf_files[0]
    print(f"Testing file: {test_file.name}")
    
    processor = PDFProcessor()
    
    try:
        text_content = processor.process(str(test_file))
        print(f"Text length: {len(text_content)}")
        print("="*50)
        print("First 1000 characters:")
        print(text_content[:1000])
        print("="*50)
        print("Text (lowercased) contains:")
        text_lower = text_content.lower()
        
        keywords = [
            'banco industrial', 'industrial', 'tarjeta', 'credit', 
            'cuenta corriente', 'checking', 'bam', 'gyt', 'g&t'
        ]
        
        for keyword in keywords:
            if keyword in text_lower:
                print(f"  ✓ '{keyword}' found")
            else:
                print(f"  ✗ '{keyword}' NOT found")
                
    except Exception as e:
        print(f"Error processing PDF: {e}")

if __name__ == "__main__":
    test_pdf_content()