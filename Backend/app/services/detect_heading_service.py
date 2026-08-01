from app.services.gemini_service import GeminiService
from docx import Document

class DetectHeadingService:
    def __init__(self):
        self.gemini_service = GeminiService()

    def detect_heading(self, word_path):
        # Step 1: Get the Gemini response
        response = self.gemini_service.analyze_document_headings(word_path)
        print("Gemini Response:")
        print(response)

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

        # Iterate through paragraphs and update their styles
        for paragraph in doc.paragraphs:
            print("Paragraph text:", paragraph.text)  # Debug: Show paragraph text
            text = paragraph.text.strip()

            # Check if any heading text is contained within the paragraph
            for level, texts in headings.items():
                for heading_text in texts:
                    if heading_text in text:  # Check if heading text is part of the paragraph
                        paragraph.style = f"Heading {level}"  # Set paragraph style to the heading level
                        print(f"Set heading level {level} for paragraph: {text}")  # Debug: Log the action
                        break  # No need to check further once a match is found

        # Save the updated document
        doc.save(word_path)
        print(f"Updated heading levels in the document: {word_path}")