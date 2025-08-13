import os
import tempfile
from PIL import Image
import pytesseract
import PyPDF2
import io

class FileProcessor:
    def __init__(self):
        """Initialize the file processor"""
        self.supported_image_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']
        self.supported_text_formats = ['.txt']
        self.supported_pdf_formats = ['.pdf']
    
    def extract_text(self, file_path, file_type):
        """
        Extract text from various file formats
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_type.startswith('image/') or file_extension in self.supported_image_formats:
                return self._extract_text_from_image(file_path)
            elif file_type == 'application/pdf' or file_extension in self.supported_pdf_formats:
                return self._extract_text_from_pdf(file_path)
            elif file_type.startswith('text/') or file_extension in self.supported_text_formats:
                return self._extract_text_from_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            # Open and process the image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR using pytesseract
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}. Make sure pytesseract is properly installed.")
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        try:
            text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _extract_text_from_text_file(self, text_path):
        """Extract text from plain text file"""
        try:
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(text_path, 'r', encoding=encoding) as file:
                        return file.read().strip()
                except UnicodeDecodeError:
                    continue
            
            raise Exception("Could not decode text file with any supported encoding")
            
        except Exception as e:
            raise Exception(f"Text file extraction failed: {str(e)}")
    
    def validate_file(self, file_path, file_type):
        """
        Validate if the file can be processed
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size (limit to 10MB)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, "File size exceeds 10MB limit"
            
            # Check if file type is supported
            file_extension = os.path.splitext(file_path)[1].lower()
            
            supported_extensions = (
                self.supported_image_formats + 
                self.supported_text_formats + 
                self.supported_pdf_formats
            )
            
            if not (file_type.startswith(('image/', 'text/', 'application/pdf')) or 
                   file_extension in supported_extensions):
                return False, f"Unsupported file type: {file_type}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_file_info(self, file_path):
        """
        Get basic information about the file
        """
        try:
            file_stats = os.stat(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            return {
                'size': file_stats.st_size,
                'extension': file_extension,
                'modified': file_stats.st_mtime
            }
            
        except Exception as e:
            return {'error': str(e)}
