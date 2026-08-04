import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from docx import Document
from google.api_core.exceptions import ResourceExhausted

from app.controllers.get_standard_word import GetStandardWord, PROCESSING_LOCK
from app.services.gemini_service import GeminiRateLimitError, GeminiService
from app.services.pdf_to_standardword_service import PdfToStandardWordService


class QuotaExceededClient:
    def generate_content(self, *_args, **_kwargs):
        raise ResourceExhausted("quota exhausted")


class QuotaExceededClientFactory:
    def create_client(self, *_args, **_kwargs):
        return QuotaExceededClient()


class StaticParser:
    def parse_args(self):
        return {"user_id": 1, "file_path": "input.pdf"}


class QuotaExceededService:
    def get_result(self, _file_path):
        raise GeminiRateLimitError("Gemini quota exhausted")


class UnexpectedFailureService:
    def get_result(self, _file_path):
        raise RuntimeError("unexpected failure")


class GeminiErrorHandlingTest(unittest.TestCase):
    def test_resource_exhausted_becomes_rate_limit_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_path = Path(temp_dir) / "input.docx"
            doc = Document()
            doc.add_paragraph("Nội dung kiểm thử")
            doc.save(doc_path)

            service = GeminiService.__new__(GeminiService)
            service.model_name = "test-model"
            service.temperature = 0
            service.request_timeout = 1
            service.client_factory = QuotaExceededClientFactory()

            with self.assertRaises(GeminiRateLimitError):
                service.analyze_document_headings(doc_path)

    def test_controller_returns_http_429_for_gemini_quota(self):
        resource = GetStandardWord.__new__(GetStandardWord)
        resource.parser = StaticParser()
        resource.service = QuotaExceededService()

        payload, status_code = resource.post()

        self.assertEqual(status_code, 429)
        self.assertIn("quota", payload["message"].casefold())
        self.assertTrue(PROCESSING_LOCK.acquire(blocking=False))
        PROCESSING_LOCK.release()

    def test_controller_returns_http_503_while_backend_is_busy(self):
        resource = GetStandardWord.__new__(GetStandardWord)
        resource.parser = StaticParser()
        resource.service = UnexpectedFailureService()

        PROCESSING_LOCK.acquire()
        try:
            payload, status_code, headers = resource.post()
        finally:
            PROCESSING_LOCK.release()

        self.assertEqual(status_code, 503)
        self.assertEqual(headers["Retry-After"], "30")
        self.assertIn("đang xử lý", payload["message"].casefold())

    def test_controller_releases_lock_after_unexpected_error(self):
        resource = GetStandardWord.__new__(GetStandardWord)
        resource.parser = StaticParser()
        resource.service = UnexpectedFailureService()

        payload, status_code = resource.post()

        self.assertEqual(status_code, 500)
        self.assertIn("unexpected failure", payload["message"])
        self.assertTrue(PROCESSING_LOCK.acquire(blocking=False))
        PROCESSING_LOCK.release()

    def test_pipeline_returns_docx_when_heading_quota_is_exhausted(self):
        service = PdfToStandardWordService.__new__(PdfToStandardWordService)
        service.convert_pdf_to_word_service = Mock()
        service.delete_footnote_service = Mock()
        service.detect_heading_service = Mock()
        service.detect_heading_service.detect_heading.side_effect = (
            GeminiRateLimitError("quota exhausted")
        )
        service.set_vietnamese_service = Mock()

        word_path, warnings = service.convert_pdf_to_standardword(
            "input.pdf",
            "output.docx",
        )

        self.assertEqual(word_path, "output.docx")
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0]["code"],
            "heading_detection_skipped_quota",
        )
        service.set_vietnamese_service.set_vietnamese_language.assert_called_once_with(
            "output.docx"
        )


if __name__ == "__main__":
    unittest.main()
