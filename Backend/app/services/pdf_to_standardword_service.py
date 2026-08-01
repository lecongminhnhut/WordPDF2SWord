import fitz
from docx import Document
from docx.shared import Inches
import os
import re
from app.services.convert_pdf_to_word_service import ConvertPdfToWordService
from app.services.detect_heading_service import DetectHeadingService
from app.services.delete_footnote_service import DeleteFootnoteService
from app.services.set_vietnamese_language_service import SetVietnameseService

class PdfToStandardWordService:
    def __init__(self):
        self.convert_pdf_to_word_service = ConvertPdfToWordService()
        self.detect_heading_service = DetectHeadingService()
        self.delete_footnote_service = DeleteFootnoteService()
        self.set_vietnamese_service = SetVietnameseService()

    def convert_pdf_to_standardword(self, pdf_path, word_path=None):
        # Determine the Word file path if not provided
        if word_path is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]  # Get the file name without extension
            word_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}.docx")
    
        # Convert the PDF file to a DOCX file
        self.convert_pdf_to_word_service.convert_pdf_to_word(pdf_path, word_path)

        # Detect headings in the DOCX file
        self.detect_heading_service.detect_heading(word_path)

        # Remove footnotes and content after horizontal lines in the DOCX file
        self.delete_footnote_service.remove_footnotes_precisely(word_path)

        # Set the Vietnamese language for the DOCX file
        self.set_vietnamese_service.set_vietnamese_language(word_path)

        return word_path