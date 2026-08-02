from collections import Counter
import re
import unicodedata

from docx import Document
import fitz


class PdfHasNoTextLayerError(ValueError):
    """Raised when a PDF does not contain enough extractable text."""


class ConvertPdfToWordService:
    """Convert text-layer PDFs to image-free, conservatively cleaned DOCX files."""

    MARGIN_RATIO = 0.20
    MAX_REPEATED_MARGIN_CHARACTERS = 160
    MAX_REPEATED_MARGIN_WORDS = 20
    MIN_REPEATED_PAGES = 3

    URL_PATTERN = re.compile(
        r"""
        (?:
            (?:https?://|ftp://|www\.)[^\s<>{}\[\](),;!?]+
            |
            (?<![@\w])
            (?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+
            (?:com|net|org|vn|edu|gov|info|biz|io|me|co|tv|book)
            (?:\.[a-z]{2})?
            (?:/[^\s<>{}\[\](),;!?]*)?
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    EMPTY_SOURCE_LABEL_PATTERN = re.compile(
        r"^(?:nguồn|source|website|ebook|tải\s+ebook\s+tại)\s*:?\s*$",
        re.IGNORECASE,
    )
    PAGE_NUMBER_PATTERN = re.compile(
        r"^(?:(?:trang|page)\s+)?(?:\d{1,5}|[ivxlcdm]{1,12})$",
        re.IGNORECASE,
    )
    STRUCTURAL_HEADING_PATTERN = re.compile(
        r"^(?:chương|phần|quyển|bài|mục|chapter|part|book)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize("NFC", value or "")
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _comparison_key(cls, value):
        return cls._normalize(value).casefold()

    @classmethod
    def _remove_urls(cls, value):
        cleaned = cls.URL_PATTERN.sub("", value or "")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned).strip()
        if cls.EMPTY_SOURCE_LABEL_PATTERN.fullmatch(cleaned):
            return ""
        return cleaned

    @classmethod
    def _extract_text_blocks(cls, page):
        page_data = page.get_text("dict")
        text_blocks = []

        for block in page_data.get("blocks", []):
            if block.get("type") != 0:
                continue

            lines = []
            for line in block.get("lines", []):
                line_text = "".join(
                    span.get("text", "") for span in line.get("spans", [])
                )
                line_text = cls._normalize(line_text)
                if line_text:
                    lines.append(line_text)

            block_text = cls._normalize(" ".join(lines))
            if block_text:
                text_blocks.append({
                    "text": block_text,
                    "bbox": tuple(block.get("bbox", (0, 0, 0, 0))),
                    "page_height": page.rect.height,
                })

        return text_blocks

    @classmethod
    def _is_margin_block(cls, block):
        _, y0, _, y1 = block["bbox"]
        page_height = block["page_height"]
        return (
            y1 <= page_height * cls.MARGIN_RATIO
            or y0 >= page_height * (1 - cls.MARGIN_RATIO)
        )

    @classmethod
    def _is_short_margin_candidate(cls, block):
        text = cls._normalize(block["text"])
        return (
            cls._is_margin_block(block)
            and len(text) <= cls.MAX_REPEATED_MARGIN_CHARACTERS
            and len(text.split()) <= cls.MAX_REPEATED_MARGIN_WORDS
        )

    @classmethod
    def _find_repeated_margin_keys(cls, pages):
        page_counts = Counter()

        for blocks in pages:
            keys_on_page = {
                cls._comparison_key(block["text"])
                for block in blocks
                if cls._is_short_margin_candidate(block)
            }
            page_counts.update(keys_on_page)

        return {
            key
            for key, count in page_counts.items()
            if key and count >= cls.MIN_REPEATED_PAGES
        }

    @classmethod
    def _should_remove_margin_block(
        cls,
        block,
        repeated_margin_keys,
        kept_structural_keys,
    ):
        if not cls._is_margin_block(block):
            return False

        text = cls._normalize(block["text"])
        if cls.PAGE_NUMBER_PATTERN.fullmatch(text):
            return True

        key = cls._comparison_key(text)
        if key not in repeated_margin_keys:
            return False

        if cls.STRUCTURAL_HEADING_PATTERN.match(text):
            if key not in kept_structural_keys:
                kept_structural_keys.add(key)
                return False

        return True

    def convert_pdf_to_word(self, pdf_path, word_path):
        with fitz.open(pdf_path) as pdf_file:
            pages = [
                self._extract_text_blocks(pdf_file.load_page(page_index))
                for page_index in range(len(pdf_file))
            ]

            extracted_text = "".join(
                block["text"] for blocks in pages for block in blocks
            )
            minimum_text_length = max(50, len(pdf_file) * 20)
            if len(extracted_text) < minimum_text_length:
                raise PdfHasNoTextLayerError(
                    "PDF không có đủ lớp văn bản để xử lý. "
                    "Công cụ hiện chưa hỗ trợ PDF scan hoặc PDF chủ yếu chứa hình ảnh."
                )

            repeated_margin_keys = self._find_repeated_margin_keys(pages)
            kept_structural_keys = set()
            doc = Document()

            for blocks in pages:
                for block in blocks:
                    if self._should_remove_margin_block(
                        block,
                        repeated_margin_keys,
                        kept_structural_keys,
                    ):
                        continue

                    paragraph_text = self._remove_urls(block["text"])
                    if paragraph_text:
                        doc.add_paragraph(paragraph_text)

            doc.save(word_path)
