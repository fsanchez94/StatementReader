from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, date

class BaseParser(ABC):
    def __init__(self, pdf_path, is_spouse=False):
        self.pdf_path = pdf_path
        self.is_spouse = is_spouse
        
    @abstractmethod
    def extract_data(self):
        """Extract data from PDF and return as a list of dictionaries"""
        pass
    
    def _convert_to_excel_date(self, date_obj):
        """Convert a date to Excel's numeric format (days since 1900-01-01)"""
        if isinstance(date_obj, date):
            # Convert to datetime for Excel compatibility
            dt = datetime.combine(date_obj, datetime.min.time())
            # Convert to Excel numeric date (days since 1900-01-01)
            return (dt - datetime(1900, 1, 1)).days + 2  # +2 for Excel's date system
        return date_obj
    
    def to_csv(self, output_path):
        """Convert extracted data to CSV"""
        data = self.extract_data()
        df = pd.DataFrame(data)
        
        # Convert dates to Excel numeric format
        if 'Date' in df.columns:
            df['Date'] = df['Date'].apply(self._convert_to_excel_date)
            
        df.to_csv(output_path, index=False)