from app.services.gemini_service import GeminiService
from docx import Document
import re
import unicodedata


def normalize_text(value):
    """Normalize text without changing its words or punctuation."""
    value = unicodedata.normalize("NFC", value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip().casefold()

class DetectHeadingService:
    def __init__(self):
        self.gemini_service = GeminiService()

    def detect_heading(self, word_path):
        # Step 1: Get the Gemini response
        response = self.gemini_service.analyze_document_headings(word_path)

        # Step 2: Parse Gemini response into heading levels
        headings = self.parse_gemini_response(response)

        # Step 3: Update the Word document with heading levels
        self.set_heading_levels(word_path, headings)

    def parse_gemini_response(self, response):
        """
        Parse the Gemini response into a dictionary of heading levels and texts.
        :param response: The text response from Gemini.
        :return: Dictionary with heading levels as keys and lists of heading texts as values.
        """
        headings = {}
        for line in response.splitlines():
            if line.startswith("Heading"):
                level, texts = line.split(":", 1)
                level = level.strip().split()[-1]  # Extract the heading level (e.g., "1", "2")
                texts = texts.strip().strip('"').split('", "')  # Split the headings into a list
                headings[level] = texts
        return headings

    def set_heading_levels(self, word_path, headings):
        """
        Set heading levels in the Word document based on detected headings.
        :param word_path: Path to the Word document.
        :param headings: Dictionary with heading levels as keys and lists of heading texts as values.
        """
        # Load the Word document
        doc = Document(word_path)

        heading_map = {}
        for level, texts in headings.items():
            if level not in {'1', '2', '3'}:
                continue

            for heading_text in texts:
                normalized_heading = normalize_text(heading_text)
                if normalized_heading:
                    heading_map.setdefault(normalized_heading, level)

        # Iterate through paragraphs and update their styles
        for paragraph in doc.paragraphs:
            normalized_text = normalize_text(paragraph.text)
            level = heading_map.get(normalized_text)

            if level:
                paragraph.style = f"Heading {level}"

        # Save the updated document
        doc.save(word_path)
