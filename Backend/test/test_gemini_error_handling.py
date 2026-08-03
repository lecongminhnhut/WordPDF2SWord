import tempfile
import unittest
from pathlib import Path

from docx import Document
from google.api_core.exceptions import ResourceExhausted

from app.controllers.get_standard_word import GetStandardWord
from app.services.gemini_service import GeminiRateLimitError, GeminiService


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


if __name__ == "__main__":
    unittest.main()
