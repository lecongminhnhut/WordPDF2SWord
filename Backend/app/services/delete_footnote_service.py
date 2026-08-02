import re
import unicodedata

from docx import Document


class DeleteFootnoteService:
    """Remove only high-confidence rendered footnote/endnote blocks.

    PDF text extraction turns notes into ordinary paragraphs, so Word does not
    retain enough semantic information to identify every possible note format.
    This service deliberately prefers leaving an unknown note in place over
    deleting book content by mistake.
    """

    NOTE_HEADING_PATTERN = re.compile(
        r"""
        ^(?:
            chú\s*thích
            |ghi\s*chú
            |cước\s*chú
            |footnotes?
            |endnotes?
            |headnotes?
        )
        (?:\s+(?:cuối\s+)?(?:trang|chương|phần|sách|tài\s*liệu))?
        \s*:?\s*$
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    NOTE_ITEM_PATTERN = re.compile(
        r"""
        ^\s*(?:
            \(\s*\d{1,4}\s*\)
            |\[\s*\d{1,4}\s*\]
            |\d{1,4}\s*[.)]
            |[*†‡]
        )\s*\S
        """,
        re.VERBOSE,
    )
    SEPARATOR_PATTERN = re.compile(r"^[\s_\-=—–―─•·*]{3,}$")

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize("NFC", value or "")
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _is_note_heading(cls, value):
        return bool(cls.NOTE_HEADING_PATTERN.fullmatch(cls._normalize(value)))

    @classmethod
    def _is_note_item(cls, value):
        return bool(cls.NOTE_ITEM_PATTERN.match(cls._normalize(value)))

    @classmethod
    def _is_separator(cls, value):
        return bool(cls.SEPARATOR_PATTERN.fullmatch(cls._normalize(value)))

    @staticmethod
    def _remove_paragraph(paragraph):
        element = paragraph._element
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    def _find_note_block(self, paragraphs, heading_index):
        """Return paragraph indexes for a confirmed, conservatively bounded block."""
        block_indexes = {heading_index}
        pending_blank_indexes = []
        found_note_item = False
        index = heading_index + 1

        while index < len(paragraphs):
            text = self._normalize(paragraphs[index].text)

            if not text:
                pending_blank_indexes.append(index)
                index += 1
                continue

            if self._is_note_item(text):
                found_note_item = True
                block_indexes.update(pending_blank_indexes)
                pending_blank_indexes = []
                block_indexes.add(index)
                index += 1
                continue

            break

        if not found_note_item:
            return set()

        if heading_index > 0 and self._is_separator(
            paragraphs[heading_index - 1].text
        ):
            block_indexes.add(heading_index - 1)

        return block_indexes

    def remove_footnotes_precisely(self, doc_path):
        """Remove recognized note blocks in-place without rebuilding the DOCX.

        A block is removed only when an exact note heading is followed by at
        least one numbered or symbolic note item. Processing stops at the first
        non-empty paragraph that is not another note item.
        """
        doc = Document(doc_path)
        paragraphs = list(doc.paragraphs)
        indexes_to_remove = set()
        blocks_removed = 0

        for index, paragraph in enumerate(paragraphs):
            if index in indexes_to_remove or not self._is_note_heading(paragraph.text):
                continue

            block_indexes = self._find_note_block(paragraphs, index)
            if block_indexes:
                indexes_to_remove.update(block_indexes)
                blocks_removed += 1

        for index in sorted(indexes_to_remove, reverse=True):
            self._remove_paragraph(paragraphs[index])

        if indexes_to_remove:
            doc.save(doc_path)

        return {
            "blocks_removed": blocks_removed,
            "paragraphs_removed": len(indexes_to_remove),
        }
