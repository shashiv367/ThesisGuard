"""
Seed the database with source documents so the plagiarism engine has
something to compare against.

Usage:
    python scripts/seed_sources.py

This script:
  1. Creates several source text documents covering different academic topics
  2. Chunks them using the extraction service
  3. Indexes them into PostgreSQL/pgvector as 'source' documents
  4. Creates a test PDF that contains both verbatim copies and paraphrased
     passages from the sources, so you can upload it via the frontend
     and see plagiarism detected.
"""

import os
import sys
import fitz  # PyMuPDF

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.extraction_service import chunk_text
from app.services.db_service import save_document
from app.services.semantic_service import index_source_document

# ──────────────────────────────────────────────────────────────
# SOURCE DOCUMENTS — these get indexed into the database
# ──────────────────────────────────────────────────────────────

SOURCE_DOCUMENTS = {
    "source_machine_learning.txt": (
        "Machine learning is a subset of artificial intelligence that focuses on building "
        "systems that learn from data. Unlike traditional programming where rules are explicitly "
        "coded, machine learning algorithms identify patterns in data and make decisions with "
        "minimal human intervention. Supervised learning uses labeled datasets to train algorithms "
        "that classify data or predict outcomes accurately. Unsupervised learning finds hidden "
        "patterns in data without pre-existing labels. Deep learning, a specialized subset of "
        "machine learning, uses neural networks with many layers to analyze various factors of "
        "data. Convolutional neural networks are particularly effective for image recognition tasks "
        "while recurrent neural networks excel at sequential data processing such as natural "
        "language processing. The backpropagation algorithm is the primary method used to train "
        "neural networks by computing gradients of the loss function. Transfer learning allows "
        "models trained on one task to be repurposed for a related task, significantly reducing "
        "training time and data requirements."
    ),
    "source_plagiarism_detection.txt": (
        "Plagiarism detection systems have evolved significantly over the past two decades. "
        "Early systems relied primarily on exact string matching and fingerprinting techniques "
        "to identify copied content. These methods, while effective for verbatim copying, were "
        "easily defeated by simple paraphrasing or synonym substitution. Modern plagiarism "
        "detection engines employ semantic similarity analysis using dense vector representations "
        "of text. Sentence-level embeddings capture the meaning of text passages regardless of "
        "surface-level word choices. Cosine similarity between embedding vectors provides a "
        "robust measure of semantic overlap between documents. The combination of lexical and "
        "semantic approaches creates a hybrid detection system that catches both exact copying "
        "and intelligent paraphrasing. N-gram shingling with MinHash signatures enables efficient "
        "approximate matching across large document corpora. Academic integrity is a cornerstone "
        "of higher education, and automated detection tools play a critical role in maintaining "
        "scholarly standards across institutions worldwide."
    ),
    "source_database_systems.txt": (
        "Relational database management systems organize data into tables with rows and columns "
        "following a strict schema. SQL remains the standard language for querying relational "
        "databases, providing powerful capabilities for data manipulation and retrieval. "
        "PostgreSQL is an advanced open-source relational database known for its reliability, "
        "feature robustness, and extensibility. It supports advanced data types including JSON, "
        "arrays, and through extensions like pgvector, high-dimensional vector data for similarity "
        "search operations. Indexing strategies such as B-tree, hash, and HNSW significantly "
        "improve query performance on large datasets. NoSQL databases emerged as alternatives "
        "for handling unstructured or semi-structured data at scale. Document stores like MongoDB "
        "use flexible schemas that can evolve over time. The CAP theorem states that a distributed "
        "database system can only simultaneously provide two of three guarantees: consistency, "
        "availability, and partition tolerance."
    ),
    "source_cybersecurity.txt": (
        "Cybersecurity encompasses the practices, technologies, and processes designed to protect "
        "networks, devices, programs, and data from attack, damage, or unauthorized access. "
        "The CIA triad of confidentiality, integrity, and availability forms the foundation of "
        "information security policies. Encryption algorithms transform readable data into encoded "
        "formats that can only be decoded with the correct key. Symmetric encryption uses a single "
        "key for both encryption and decryption, while asymmetric encryption employs a pair of "
        "public and private keys. Firewalls act as barriers between trusted internal networks and "
        "untrusted external networks, filtering traffic based on predefined security rules. "
        "Intrusion detection systems monitor network traffic for suspicious activity and known "
        "threat signatures. Social engineering attacks exploit human psychology rather than "
        "technical vulnerabilities, making employee training a critical component of any security "
        "strategy. Multi-factor authentication adds additional verification layers beyond simple "
        "passwords to protect sensitive systems and accounts."
    ),
}


# ──────────────────────────────────────────────────────────────
# TEST DOCUMENT — contains plagiarised content from the sources
# ──────────────────────────────────────────────────────────────

TEST_DOCUMENT_TEXT = """A Study on Modern Computing Technologies

Chapter 1: Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. Unlike traditional programming where rules are explicitly coded, machine learning algorithms identify patterns in data and make decisions with minimal human intervention. This technology has revolutionized many industries in recent years.

Chapter 2: Detecting Academic Dishonesty

Modern plagiarism detection engines employ semantic similarity analysis using dense vector representations of text. Sentence-level embeddings capture the meaning of text passages regardless of surface-level word choices. Cosine similarity between embedding vectors provides a robust measure of semantic overlap between documents.

Chapter 3: Information Security Fundamentals

The protection of digital systems involves practices and technologies designed to safeguard networks and data from unauthorized access or damage. The fundamental principles of confidentiality, integrity, and availability guide security policies across organizations. Encryption techniques convert readable information into encoded formats requiring special keys for decryption.

Chapter 4: Database Technologies

PostgreSQL is an advanced open-source relational database known for its reliability, feature robustness, and extensibility. It supports advanced data types including JSON, arrays, and through extensions like pgvector, high-dimensional vector data for similarity search operations.

Chapter 5: Original Analysis

This chapter presents our original findings from experiments conducted over six months. We developed a novel framework for evaluating cross-domain transfer learning performance. Our results indicate that pre-trained models can achieve up to 94 percent accuracy on domain-specific tasks with minimal fine-tuning, challenging the conventional wisdom that domain-specific training data is always necessary.

Chapter 6: Conclusion

In conclusion, the rapid advancement of computing technologies continues to reshape academic research and professional practice. The intersection of machine learning, database systems, and cybersecurity presents exciting opportunities for future investigation.
"""


def seed_sources():
    """Index all source documents into the database."""
    print("=" * 60)
    print("  ThesisGuard — Seeding Source Documents")
    print("=" * 60)

    for filename, text in SOURCE_DOCUMENTS.items():
        chunks = chunk_text(text)
        doc_id = save_document(filename, "source")
        index_source_document(doc_id, chunks)
        print(f"  [OK] Indexed '{filename}' -> document_id={doc_id}, {len(chunks)} chunks")

    print(f"\n  Total: {len(SOURCE_DOCUMENTS)} source documents indexed.\n")


def create_test_pdf():
    """Create a test PDF with plagiarised content for uploading via the frontend."""
    os.makedirs("test_docs", exist_ok=True)
    pdf_path = os.path.join("test_docs", "test_plagiarised_paper.pdf")

    doc = fitz.open()
    
    # Split into pages (rough split by chapters)
    paragraphs = [p.strip() for p in TEST_DOCUMENT_TEXT.strip().split("\n\n") if p.strip()]
    
    # Put content on pages (roughly 3 paragraphs per page)
    page_size = 3
    for page_start in range(0, len(paragraphs), page_size):
        page = doc.new_page(width=595, height=842)  # A4
        page_text = "\n\n".join(paragraphs[page_start:page_start + page_size])
        page.insert_textbox(
            fitz.Rect(50, 50, 545, 792),
            page_text,
            fontsize=11,
            fontname="helv",
        )

    doc.save(pdf_path)
    doc.close()
    print(f"  [OK] Created test PDF: {os.path.abspath(pdf_path)}")
    print(f"    Upload this file via the frontend to see plagiarism results.\n")
    print("    What's inside:")
    print("    * Ch.1 -- VERBATIM copy from source_machine_learning.txt")
    print("    * Ch.2 -- VERBATIM copy from source_plagiarism_detection.txt")
    print("    * Ch.3 -- PARAPHRASED from source_cybersecurity.txt")
    print("    * Ch.4 -- VERBATIM copy from source_database_systems.txt")
    print("    * Ch.5 -- ORIGINAL content (should NOT be flagged)")
    print("    * Ch.6 -- ORIGINAL conclusion (should NOT be flagged)")

    return pdf_path


if __name__ == "__main__":
    print()
    seed_sources()
    create_test_pdf()
    print("=" * 60)
    print("  Done! Start the server and upload test_plagiarised_paper.pdf")
    print("=" * 60)
    print()
