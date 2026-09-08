import re
import pymupdf  # PyMuPDF
import docx
import nltk
from nltk.tokenize import sent_tokenize

# Ensure the punkt tokenizer models are downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

def extract_text_pdf(path: str) -> str:
    """Extracts raw text from a PDF."""
    doc = pymupdf.open(path)
    return "\n".join(page.get_text() for page in doc)

def extract_text_docx(path: str) -> str:
    """Extracts paragraph text from a DOCX."""
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text(path: str) -> str:
    """Dispatches extraction based on file extension."""
    if path.lower().endswith(".pdf"):
        return extract_text_pdf(path)
    elif path.lower().endswith(".docx"):
        return extract_text_docx(path)
    else:
        raise ValueError(f"Unsupported file type for {path}")

def clean_text(text: str) -> str:
    """Normalizes whitespace."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text: str, sentences_per_chunk: int = 4, overlap: int = 1) -> list:
    """Splits cleaned text into overlapping sentence-window chunks."""
    sentences = sent_tokenize(clean_text(text))
    chunks = []
    
    if len(sentences) == 0:
        return chunks
        
    step = max(1, sentences_per_chunk - overlap)
    
    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        if chunk:
            chunks.append(chunk)
            
        # Break if we've reached the end of sentences
        if i + sentences_per_chunk >= len(sentences):
            break
            
    return chunks
