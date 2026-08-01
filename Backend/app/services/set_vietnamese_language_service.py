from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

class SetVietnameseService:
    def __init__(self):
        pass

    def set_vietnamese_language(self, doc_path):
        """
        Set the document's default language to Vietnamese.
        """
        doc = Document(doc_path)
        
        # Access the styles element
        styles_element = doc.styles.element

        # Find or create the docDefaults element
        docDefaults = styles_element.find(qn('w:docDefaults'))
        if docDefaults is None:
            docDefaults = OxmlElement('w:docDefaults')
            styles_element.append(docDefaults)
        
        # Find or create w:rPrDefault
        rPrDefault = docDefaults.find(qn('w:rPrDefault'))
        if rPrDefault is None:
            rPrDefault = OxmlElement('w:rPrDefault')
            docDefaults.append(rPrDefault)
        
        # Find or create w:rPr
        rPr = rPrDefault.find(qn('w:rPr'))
        if rPr is None:
            rPr = OxmlElement('w:rPr')
            rPrDefault.append(rPr)
        
        # Find or create w:lang
        lang = rPr.find(qn('w:lang'))
        if lang is None:
            lang = OxmlElement('w:lang')
            rPr.append(lang)
        
        # Define the Vietnamese language code
        lang_code = "vi-VN"
        
        # Set the language attributes
        lang.set(qn('w:val'), lang_code)         # For normal text
        lang.set(qn('w:eastAsia'), lang_code)    # For East Asian text
        lang.attrib.pop(qn('w:bidi'), None)

        # Save the modified document
        doc.save(doc_path)
