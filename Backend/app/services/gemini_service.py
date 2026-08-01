from docx import Document
from app.main.settings import Config
import google.generativeai as genai
import time


class GeminiPrompt:
    class SystemContent:
        analyze_headings = """
        You are an assistant specializing in text analysis. Your task is to analyze the text of a document and categorize headings based on their levels. 
        Return the result in the following format:
        Heading 1: "Text 1", "Text 2", "Text 3"
        Heading 2: "Text 1", "Text 2", "Text 3"
        Heading 3: "Text 1", "Text 2", "Text 3"
        The heading is often short. Some elements within headings like "Quyển", "Chương", "Phần", "Mục", "Bài", "Lịch sử", "Phát triển", "Tác động", "Ứng dụng", "Kết luận", "Tổng quan", "Phương pháp", "Đề xuất", "Giải pháp". 
        You should include the full heading content. If any level not exist, no need to return that level.
        Focus on detecting clear and meaningful headings that organize the content logically.
        """

    class UserContent:
        @staticmethod
        def analyze_headings(document_text):
            return f"""
            Analyze the following text to identify headings and group them by levels:
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
        self.temperature = 0.7
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
        """
        Analyze a Word document to extract and group headings by levels using Gemini AI.

        :param doc_path: Path to the Word document.
        :return: Result from Gemini AI as a string.
        """
        # Load the Word document and extract its text
        doc = Document(doc_path)
        document_text = "\n".join([paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()])

        # Create client with appropriate instructions
        client_kwargs = self.client_kwargs(GeminiPrompt.SystemContent.analyze_headings)
        client = self.client_factory.create_client('google', **client_kwargs)

        # Generate the prompt for Gemini
        user_instruction = GeminiPrompt.UserContent.analyze_headings(document_text)

        # Call the generative model to analyze headings
        response = client.generate_content(user_instruction, stream=True)
        response.resolve()
        time.sleep(0.5)

        return response.text.strip()