# ThesisGuard — AI-Based Semantic Plagiarism Detection Engine
### Full Technical Documentation & Implementation Guide
**Final Year Project — Department of Computer Science & Engineering**
**Scope covered in this document: the plagiarism detection engine only** (workflow/SaaS platform is out of scope for this semester).

---

## 1. Project Overview

ThesisGuard's plagiarism engine is a self-hosted system that detects both verbatim copying and paraphrased (semantic) plagiarism in academic documents, without relying on paid third-party APIs. It combines two complementary detection layers — exact lexical matching and semantic similarity via sentence embeddings — and adds two supporting AI features: automatic keyword extraction (for fast candidate filtering and topic tagging) and automatic source-document summarization (so a reviewer understands *why* a match was flagged without opening the source file).

**One-line description:** Upload a document → it's chunked and compared against a reference corpus using both n-gram overlap and semantic embeddings → a report is generated showing matched passages, similarity scores, match type (exact/paraphrased), source summaries, and keyword tags.

---

## 2. Existing Systems and Their Limitations

| System | Method | Limitation |
|---|---|---|
| Turnitin / iThenticate | Fingerprint / n-gram matching against licensed corpus | Weak against paraphrased text; documents leave institutional control (cloud-hosted); per-document licensing cost |
| PlagScan / Ouriginal | Similar string/fingerprint-based matching | Same paraphrase blind spot; subscription cost scales badly for institutions |
| Generic keyword/TF-IDF tools | Bag-of-words overlap | No understanding of meaning; trivially defeated by synonym substitution |
| Manual review | Human reading | Not scalable; inconsistent; misses subtle paraphrase |

**Common gap across all of the above:** none combine cost-free self-hosting, semantic (meaning-level) detection, *and* explainable output (why something was flagged) in one system.

---

## 3. Proposed System

A two-layer, self-hosted detection pipeline:

1. **Exact-match layer** — catches verbatim/near-verbatim copying cheaply, without any model inference.
2. **Semantic layer** — catches paraphrased plagiarism using pretrained sentence embeddings and vector similarity search.

Supporting features:
3. **Keyword extraction** — speeds up comparison at scale (pre-filtering) and provides topic tags.
4. **Abstractive summarization** — generates a short human-readable explanation of each matched source document.

### 3.1 Objectives
- Detect verbatim copying with near-100% recall using lexical matching.
- Detect paraphrased/reworded plagiarism using semantic similarity, evaluated with real precision/recall numbers (not just demo cases).
- Keep the entire pipeline self-hosted — no student document ever leaves your own infrastructure.
- Keep compute requirements CPU-only — no GPU dependency, since this must run on ordinary student hardware or a modest server.

### 3.2 Limitations (state these explicitly in your report)
- No fine-tuning: the embedding model is general-purpose, not trained on academic/thesis-specific language.
- Similarity threshold is tuned on the PAN benchmark corpus (book/Wikipedia/arXiv-sourced), not real student theses — may need retuning if deployed on institutional data.
- No OCR: scanned/image-only PDFs will not extract text.
- No cross-lingual detection.
- Heavily adversarial paraphrasing (including LLM-assisted rewriting designed specifically to evade detection) is an open research problem and may still slip past the similarity threshold.

---

## 4. System Architecture

```
                         ┌─────────────────────────┐
                         │   Uploaded Document      │
                         │   (PDF / DOCX)            │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │  Text Extraction Module   │
                         │  (PyMuPDF / python-docx)  │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │   Preprocessing & Chunking │
                         │  (clean text, 3–5 sentence │
                         │   overlapping chunks)      │
                         └────────────┬─────────────┘
                          ┌───────────┴────────────┐
                          │                         │
              ┌───────────▼───────────┐ ┌───────────▼────────────┐
              │  Exact-Match Layer     │ │   Semantic Layer         │
              │  (n-gram shingling +   │ │  (SBERT embeddings +     │
              │   MinHash / Jaccard)   │ │   pgvector similarity)   │
              └───────────┬───────────┘ └───────────┬────────────┘
                          │                         │
                          └───────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │   Match Aggregator         │
                         │  (merge + dedupe results)  │
                         └────────────┬─────────────┘
                          ┌───────────┴────────────┐
                          │                         │
              ┌───────────▼───────────┐ ┌───────────▼────────────┐
              │  Keyword Extraction    │ │  Source Summarization    │
              │  (KeyBERT)             │ │  (DistilBART, abstractive)│
              └───────────┬───────────┘ └───────────┬────────────┘
                          │                         │
                          └───────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │    Report Generator        │
                         │  (JSON + rendered report)  │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │   FastAPI REST Layer       │
                         │   + Minimal Web UI          │
                         └────────────────────────────┘
```

---

## 5. Technology Stack & Justification

| Component | Choice | Why |
|---|---|---|
| Programming language | **Python 3.10+** | Every library needed (sentence-transformers, psycopg2/pgvector, KeyBERT, HuggingFace transformers, FastAPI) is Python-native. There is no reason to introduce a second language for this scope. |
| PDF extraction | PyMuPDF (`fitz`) | Faster and more reliable text layout extraction than PyPDF2/pdfminer for typical academic PDFs. |
| DOCX extraction | `python-docx` | Standard, well-maintained, sufficient for paragraph-level extraction. |
| Exact-match detection | MinHash / n-gram Jaccard (`datasketch` or hand-rolled) | No model needed; catches verbatim copying instantly and cheaply; complements rather than duplicates the semantic layer. |
| Embedding model | **`all-MiniLM-L6-v2`** (sentence-transformers) | Small (~80MB), fast on CPU, strong general-purpose semantic similarity performance — the standard lightweight choice for this exact task in the papers reviewed. |
| Database (metadata + vectors) | **PostgreSQL 16 (local) + `pgvector` extension** | One database for everything: relational tables for documents/chunks/reports, and native vector similarity search in the same store via `pgvector`. Genuinely self-hosted — no student document or embedding ever leaves your machine/server, which matches the project's core privacy claim. Replaces the need for a separate vector database entirely. |
| Keyword extraction | **KeyBERT** | Built directly on sentence-transformers — reuses the same embedding model you already have loaded, no new dependency to learn. |
| Summarization | **`sshleifer/distilbart-cnn-12-6`** (HuggingFace) | Distilled version of BART; abstractive summarization that runs tolerably on CPU, no fine-tuning required. |
| Evaluation dataset | **PAN Plagiarism Corpus** (PAN-PC-11 or a later PAN@CLEF edition) | Free for research use, comes with ground-truth labels for plagiarized spans — enables real precision/recall computation without needing a real thesis corpus. |
| Backend API | **FastAPI** | Async-friendly, automatic OpenAPI docs, minimal boilerplate compared to Django REST for a service this focused. |
| Frontend | Minimal HTML/JS or React (Vite) upload page | Full Next.js dashboard is out of scope this semester — don't build it. |
| Containerization (optional, do last) | Docker Compose | Only after the pipeline works end-to-end locally. |

**Why not Neon/Firebase:** both are viable managed clouds and pgvector works identically on Neon, but both are third-party infrastructure — using either means student documents and embeddings leave your machine, which directly contradicts the "self-hosted, data never leaves institutional control" claim in the project abstract. Local Postgres keeps that claim true. The code in this document is identical either way; only the connection string changes.

---

## 6. Module-by-Module Implementation

### 6.1 Environment Setup

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

pip install sentence-transformers psycopg2-binary pgvector keybert transformers torch \
            pymupdf python-docx fastapi uvicorn datasketch nltk python-dotenv
```

### 6.1.1 Installing PostgreSQL Locally

**Windows**
1. Download the installer from https://www.postgresql.org/download/windows/ (EDB installer).
2. Run it. When prompted, set a password for the default `postgres` superuser — write it down, you'll need it in your `.env` file.
3. Keep the default port `5432` unless it's already in use.
4. The installer offers to launch **Stack Builder** at the end — you don't need any of its extra components for this project, you can skip it.
5. Verify install: open **SQL Shell (psql)** from the Start menu, hit enter through the prompts (using defaults), and enter your password when asked. If you get a `postgres=#` prompt, it worked.

**macOS**
```bash
brew install postgresql@16
brew services start postgresql@16
```
Verify: `psql postgres` should drop you into a `postgres=#` prompt. If `psql` isn't found, add Homebrew's Postgres bin to your PATH as `brew` will instruct after install.

**Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```
Verify: `sudo -u postgres psql` should drop you into a `postgres=#` prompt.

**Create your project database (same on all platforms, from the psql prompt or a terminal):**
```sql
CREATE DATABASE thesisguard;
CREATE USER thesisguard_user WITH PASSWORD 'choose_a_password';
GRANT ALL PRIVILEGES ON DATABASE thesisguard TO thesisguard_user;
```

**Install the pgvector extension** (needed for embedding similarity search):

- *Windows*: pgvector isn't bundled with the EDB installer. Easiest path: install via [StackBuilder is not needed] — instead, download the prebuilt pgvector binaries matching your Postgres version from https://github.com/pgvector/pgvector, or if you have Visual Studio Build Tools, build from source per the repo's Windows instructions. If this gets painful, the alternative is running Postgres inside Docker Desktop using the `pgvector/pgvector:pg16` image, which comes with the extension preinstalled — one `docker run` command, no manual compilation.
- *macOS*: `brew install pgvector`
- *Linux*: `sudo apt install postgresql-16-pgvector` (package name may vary slightly by distro version; if unavailable, build from source per https://github.com/pgvector/pgvector#installation)

Then, connected to your `thesisguard` database (`psql -d thesisguard`):
```sql
CREATE EXTENSION vector;
```

Verify it worked:
```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```
You should see one row returned.

**Create a `.env` file in your project root** (never commit this file):
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=thesisguard
DB_USER=thesisguard_user
DB_PASSWORD=choose_a_password
```

### 6.1.2 Database Schema

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    doc_type TEXT CHECK (doc_type IN ('source', 'suspicious'))
);

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(384)  -- 384 = output dimension of all-MiniLM-L6-v2
);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    report_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ANN index for fast similarity search once your chunk count grows past a few thousand
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
```

Note the foreign keys (`REFERENCES ... ON DELETE CASCADE`) — this is the referential integrity a document store like MongoDB or Firestore can't give you natively, and it's exactly why Postgres fits this data better.

### 6.2 Text Extraction

```python
import fitz  # PyMuPDF
import docx

def extract_text_pdf(path):
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)

def extract_text_docx(path):
    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs)

def extract_text(path):
    if path.lower().endswith(".pdf"):
        return extract_text_pdf(path)
    elif path.lower().endswith(".docx"):
        return extract_text_docx(path)
    raise ValueError("Unsupported file type")
```

### 6.3 Preprocessing & Chunking

```python
import re
import nltk
nltk.download("punkt")
from nltk.tokenize import sent_tokenize

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text, sentences_per_chunk=4, overlap=1):
    sentences = sent_tokenize(clean_text(text))
    chunks = []
    step = sentences_per_chunk - overlap
    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks
```

### 6.4 Exact-Match Layer (n-gram / MinHash)

```python
from datasketch import MinHash, MinHashLSH

def get_minhash(text, n=5, num_perm=128):
    m = MinHash(num_perm=num_perm)
    words = text.split()
    for i in range(len(words) - n + 1):
        shingle = " ".join(words[i:i + n])
        m.update(shingle.encode("utf8"))
    return m

def build_exact_match_index(source_chunks, threshold=0.5):
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    minhashes = {}
    for idx, chunk in enumerate(source_chunks):
        mh = get_minhash(chunk)
        minhashes[idx] = mh
        lsh.insert(str(idx), mh)
    return lsh, minhashes

def check_exact_match(query_chunk, lsh, minhashes):
    q_mh = get_minhash(query_chunk)
    return lsh.query(q_mh)  # returns indices of matching source chunks
```

### 6.5 Semantic Layer (SBERT + PostgreSQL/pgvector)

```python
import os
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    register_vector(conn)
    return conn

def index_source_document(document_id, chunks):
    embeddings = model.encode(chunks)
    conn = get_connection()
    with conn.cursor() as cur:
        rows = [(document_id, i, chunk, emb.tolist())
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings))]
        execute_values(
            cur,
            "INSERT INTO chunks (document_id, chunk_index, text, embedding) VALUES %s",
            rows
        )
    conn.commit()
    conn.close()

def semantic_search(query_chunk, top_k=3):
    q_embedding = model.encode([query_chunk])[0].tolist()
    conn = get_connection()
    with conn.cursor() as cur:
        # <=> is pgvector's cosine distance operator; lower = more similar
        cur.execute(
            """
            SELECT id, document_id, chunk_index, text, 1 - (embedding <=> %s::vector) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (q_embedding, q_embedding, top_k)
        )
        results = cur.fetchall()
    conn.close()
    return results  # list of (id, document_id, chunk_index, text, similarity)
```

`1 - cosine_distance` converts pgvector's distance metric into a similarity score in the familiar 0–1 range (1 = identical), which is what you'll threshold against during evaluation.

### 6.6 Keyword Extraction (KeyBERT)

```python
from keybert import KeyBERT

kw_model = KeyBERT(model=model)  # reuse the same SBERT model

def extract_keywords(text, top_n=10):
    return kw_model.extract_keywords(
        text, keyphrase_ngram_range=(1, 2),
        stop_words="english", top_n=top_n
    )
```

Use this at ingestion time to tag each source document, and to pre-filter candidates before running full semantic search once your corpus grows past a few hundred documents.

### 6.7 Abstractive Source Summarization (DistilBART)

```python
from transformers import pipeline

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_source(text, max_length=60, min_length=20):
    # truncate long documents to model's input limit before summarizing
    truncated = text[:3000]
    result = summarizer(truncated, max_length=max_length, min_length=min_length, do_sample=False)
    return result[0]["summary_text"]
```

Run this once per source document at ingestion, cache the result — never at query time.

### 6.8 Match Aggregation & Report Generation

```python
def generate_report(query_chunks, lsh, minhashes, source_lookup):
    report = []
    for i, chunk in enumerate(query_chunks):
        exact_matches = check_exact_match(chunk, lsh, minhashes)
        semantic_results = semantic_search(chunk)

        match_type = "exact" if exact_matches else "semantic"
        report.append({
            "chunk_index": i,
            "text": chunk,
            "match_type": match_type,
            "exact_match_ids": exact_matches,
            "semantic_matches": semantic_results
        })
    return report
```

### 6.9 API Layer (FastAPI)

```python
from fastapi import FastAPI, UploadFile
import shutil

app = FastAPI()

@app.post("/check")
async def check_document(file: UploadFile):
    temp_path = f"./temp/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text(temp_path)
    chunks = chunk_text(text)
    report = generate_report(chunks, lsh, minhashes, source_lookup)
    return {"filename": file.filename, "report": report}
```

Run with: `uvicorn main:app --reload`

### 6.10 Minimal Frontend

A single HTML page with a file upload form posting to `/check`, rendering the JSON response as a table, is sufficient for this scope. Do not build a full Next.js dashboard for this module — that belongs to the workflow platform, which is out of scope this semester.

---

## 7. Evaluation Methodology

1. Download PAN-PC-11 (or a later PAN@CLEF plagiarism detection edition).
2. Run your pipeline against the suspicious/source document pairs.
3. Compare your flagged matches against PAN's ground-truth annotations (offset + length of plagiarized spans).
4. Compute:
   - **Precision** = correctly flagged matches / all flagged matches
   - **Recall** = correctly flagged matches / all actual plagiarism cases
   - **F1** = harmonic mean of precision and recall
5. Tune your similarity threshold (e.g., test 0.6, 0.7, 0.8, 0.85 cosine similarity cutoffs) and report the trade-off curve — this table, with real numbers, is your strongest evidence of engineering rigor in the final report.
6. Report separately: exact-match layer performance alone, semantic layer performance alone, and combined pipeline performance — this demonstrates the hybrid design was a deliberate, measurable choice, not decoration.

---

## 8. Implementation Timeline (16 weeks)

| Weeks | Task |
|---|---|
| 1–2 | Learn embeddings/cosine similarity basics; install and test libraries on toy examples |
| 3–4 | Text extraction + chunking pipeline, tested on real documents |
| 5–6 | Exact-match (MinHash) layer — working standalone demo |
| 7–9 | Semantic layer — SBERT + PostgreSQL/pgvector, PAN data loaded |
| 10–11 | Threshold tuning + evaluation (precision/recall/F1) |
| 12 | Merge exact + semantic layers into unified report |
| 13 | Keyword extraction (KeyBERT) integration |
| 14 | Abstractive summarization (DistilBART) integration |
| 15 | FastAPI wrapper + minimal UI, error handling |
| 16 | Buffer, documentation, viva rehearsal |

---

## 9. Future Enhancements

- AI-generated text detection (ChatGPT/LLM-written submissions) — arguably more current than paraphrase detection alone, given documented rises in LLM-assisted academic misconduct.
- Domain-specific contrastive fine-tuning once a real institutional thesis corpus becomes available.
- Cross-lingual plagiarism detection.
- AST-based structural comparison for code plagiarism (a genuinely different technique from text embeddings — treat as separate future work, not an extension of this pipeline).
- Citation/co-authorship network analysis for anomaly detection.

---

## 10. Key References

- PlagiSense — AI-based semantic plagiarism detection using Sentence-BERT embeddings and cosine similarity.
- An offline-capable semantic plagiarism detection system using Sentence-BERT with PDF chunking and web-sourced comparison.
- A hybrid TF-IDF + BERT approach combining structural and semantic similarity, addressing the real-time computational cost limitations of pure BERT-based methods.
- A semantic-syntactic hybrid framework combining Word2Vec/GloVe/FastText/BERT embeddings with syntactic similarity vectors.
- Pudasaini, S., Miralles-Pechuán, L., Lillis, D. et al. "Survey on AI-Generated Plagiarism Detection: The Impact of Large Language Models on Academic Integrity." *Journal of Academic Ethics*, 2025.
- Wu, J. et al. "A Survey on LLM-Generated Text Detection: Necessity, Methods, and Future Directions." *Computational Linguistics*, 2025.
- PAN@CLEF Plagiarism Detection Task overview papers (PAN-PC-11 and later editions) — corpus and evaluation methodology source.

---

*This document is a build reference. It does not replace a working, tested implementation — evaluation numbers from Section 7 are what actually demonstrates the system works.*
