import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pymupdf
import docx
from app.services.extraction_service import extract_text, chunk_text

def create_fixtures():
    os.makedirs("tests/fixtures", exist_ok=True)
    
    pdf_path = "tests/fixtures/sample.pdf"
    if not os.path.exists(pdf_path):
        doc = pymupdf.open()
        page = doc.new_page()
        text = (
            "This is the first sentence of our sample PDF. "
            "This is the second sentence, which provides more context. "
            "Here is the third sentence. "
            "And the fourth sentence! "
            "Let's add a fifth one to test overlap. "
            "Finally, a sixth sentence just to be sure."
        )
        page.insert_textbox(pymupdf.Rect(50, 50, 500, 500), text, fontsize=12)
        doc.save(pdf_path)
        print(f"Created {pdf_path}")
    
    docx_path = "tests/fixtures/sample.docx"
    if not os.path.exists(docx_path):
        doc = docx.Document()
        text = (
            "This is the first sentence in the Word document. "
            "This is the second sentence in Word. "
            "Here is the third sentence for Word. "
            "And the fourth sentence! "
            "Let's add a fifth one to test overlap in DOCX. "
            "And a sixth sentence."
        )
        doc.add_paragraph(text)
        doc.save(docx_path)
        print(f"Created {docx_path}")

    return pdf_path, docx_path

def run_tests():
    print("Setting up fixtures...")
    pdf_path, docx_path = create_fixtures()
    print("-" * 50)
    
    print(f"\nTesting PDF Extraction on: {pdf_path}")
    pdf_text = extract_text(pdf_path)
    print("Raw text extracted:")
    print(pdf_text)
    
    print("\nPDF Chunks (sentences_per_chunk=4, overlap=1):")
    pdf_chunks = chunk_text(pdf_text, sentences_per_chunk=4, overlap=1)
    for i, chunk in enumerate(pdf_chunks):
        print(f"Chunk {i+1}: {chunk}")
        
    print("-" * 50)
    
    print(f"\nTesting DOCX Extraction on: {docx_path}")
    docx_text = extract_text(docx_path)
    print("Raw text extracted:")
    print(docx_text)
    
    print("\nDOCX Chunks (sentences_per_chunk=4, overlap=1):")
    docx_chunks = chunk_text(docx_text, sentences_per_chunk=4, overlap=1)
    for i, chunk in enumerate(docx_chunks):
        print(f"Chunk {i+1}: {chunk}")

if __name__ == "__main__":
    run_tests()
