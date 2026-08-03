from docx import Document
from app.main.settings import Config
import google.generativeai as genai
from google.api_core.exceptions import (
    DeadlineExceeded,
    GoogleAPIError,
    ResourceExhausted,
)


class GeminiRateLimitError(RuntimeError):
    """Raised when the active Gemini project quota is exhausted."""


class GeminiPrompt:
    class SystemContent:
        analyze_headings = """
        You are an assistant specializing in Vietnamese document structure.
        Analyze the document and categorize headings by level.

        Return only lines in this exact format, without Markdown or explanations:
        Heading 1: "Text 1", "Text 2", "Text 3"
        Heading 2: "Text 1", "Text 2", "Text 3"
        Heading 3: "Text 1", "Text 2", "Text 3"

        Copy every heading verbatim from the document. Do not correct spelling,
        punctuation, capitalization, numbering, or Roman numerals. Do not return
        empty headings. Omit a heading level if it does not exist.

        Common Vietnamese heading markers include: "Quyển", "Phần", "Chương",
        "Bài", "Mục", and "Tiểu mục". Use Heading 1 for chapters or major
        sections, Heading 2 for their direct sections, and Heading 3 for
        subsections. Keep the hierarchy logical and do not skip levels.
        """

    class UserContent:
        @staticmethod
        def analyze_headings(document_text):
            return f"""
            Analyze the following text to identify headings and group them by levels.
            Copy each detected heading exactly as it appears in the source text:
            {document_text}
            """


class ClientFactory:
    def __init__(self):
        self.clients = {}

    def register_client(self, name, client_class):
        self.clients[name] = client_class

    def create_client(self, name, **kwargs):
        client_class = self.clients.get(name)
        if not client_class:
            raise ValueError(f"Client not found: {name}")
        return client_class(**kwargs)


class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL_NAME
        self.temperature = 0
        self.request_timeout = Config.GEMINI_REQUEST_TIMEOUT
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY not set in environment variables')
        genai.configure(api_key=self.api_key)
        self.client_factory = ClientFactory()
        self.client_factory.register_client('google', genai.GenerativeModel)

    def client_kwargs(self, system_instruction):
        return {
            'model_name': self.model_name,
            'generation_config': {
                'temperature': self.temperature
            },
            'system_instruction': system_instruction
        }

    def analyze_document_headings(self, doc_path):
        """Analyze a Word document and return headings grouped by level."""
        doc = Document(doc_path)
        document_text = "\n".join(
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        )

        client_kwargs = self.client_kwargs(GeminiPrompt.SystemContent.analyze_headings)
        client = self.client_factory.create_client('google', **client_kwargs)
        user_instruction = GeminiPrompt.UserContent.analyze_headings(document_text)

        try:
            response = client.generate_content(
                user_instruction,
                request_options={'timeout': self.request_timeout}
            )
            return response.text.strip()
        except DeadlineExceeded as exc:
            raise TimeoutError(
                f"Gemini không phản hồi trong {self.request_timeout} giây."
            ) from exc
        except ResourceExhausted as exc:
            raise GeminiRateLimitError(
                f"Gemini đã vượt giới hạn quota: {exc}"
            ) from exc
        except GoogleAPIError as exc:
            raise RuntimeError(f"Không thể gọi Gemini: {exc}") from exc
