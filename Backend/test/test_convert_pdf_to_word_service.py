import tempfile
import unittest
from pathlib import Path

from docx import Document
import fitz

from app.services.convert_pdf_to_word_service import ConvertPdfToWordService


class ConvertPdfToWordServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = ConvertPdfToWordService()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_pdf(self):
        pdf_path = Path(self.temp_dir.name) / "input.pdf"
        pdf = fitz.open()
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
        image.clear_with(0x336699)

        for page_number in range(1, 4):
            page = pdf.new_page(width=595, height=842)
            page.insert_text((72, 45), "REPEATED BOOK TITLE")
            page.insert_text((72, 75), "Repeated Author")
            page.insert_text((72, 105), "Chapter I")
            page.insert_text(
                (72, 250),
                f"Unique body text for page {page_number}. "
                "This is the actual book content and must remain in the document.",
            )
            page.insert_text((72, 790), f"Page {page_number}")
            page.insert_text((72, 815), "Source: thuviensach.com")
            page.insert_image(fitz.Rect(400, 300, 500, 400), pixmap=image)

        pdf.save(pdf_path)
        pdf.close()
        return pdf_path

    def test_removes_images_urls_and_repeated_margin_text(self):
        pdf_path = self.create_pdf()
        word_path = Path(self.temp_dir.name) / "output.docx"

        self.service.convert_pdf_to_word(pdf_path, word_path)

        doc = Document(word_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        combined_text = "\n".join(paragraphs)

        self.assertEqual(len(doc.inline_shapes), 0)
        self.assertNotIn("REPEATED BOOK TITLE", combined_text)
        self.assertNotIn("Repeated Author", combined_text)
        self.assertNotIn("thuviensach.com", combined_text)
        self.assertNotIn("Page 1", combined_text)
        self.assertEqual(paragraphs.count("Chapter I"), 1)
        for page_number in range(1, 4):
            self.assertIn(f"Unique body text for page {page_number}.", combined_text)

    def test_removes_links_without_deleting_surrounding_text(self):
        cleaned = self.service._remove_urls(
            "Đọc thêm tại https://thuviensach.com/book và tiếp tục nội dung."
        )

        self.assertEqual(cleaned, "Đọc thêm tại và tiếp tục nội dung.")


if __name__ == "__main__":
    unittest.main()
