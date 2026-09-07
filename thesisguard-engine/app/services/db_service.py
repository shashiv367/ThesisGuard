import os
import json
from typing import Optional, List
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Returns a psycopg2 connection with pgvector's vector type registered."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "thesisguard"),
        user=os.getenv("DB_USER", "thesisguard_user"),
        password=os.getenv("DB_PASSWORD", "choose_a_password")
    )
    register_vector(conn)
    return conn

def init_schema():
    """Initializes the database tables and indexes."""
    conn = get_connection()
    with conn.cursor() as cur:
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Create documents table (or add user_id foreign key if table already exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT NOW(),
                doc_type TEXT CHECK (doc_type IN ('source', 'suspicious', 'uploaded', 'pasted')),
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            );
            ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_doc_type_check;
            ALTER TABLE documents ADD CONSTRAINT documents_doc_type_check 
                CHECK (doc_type IN ('source', 'suspicious', 'uploaded', 'pasted'));
            ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
        """)
        
        # Create chunks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding VECTOR(384)
            );
        """)
        
        # Create reports table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                report_json JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create ANN index for fast similarity search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
            ON chunks USING hnsw (embedding vector_cosine_ops);
        """)
    conn.commit()
    conn.close()

def create_user(email: str, hashed_password: str) -> dict:
    """Inserts a new user and returns their id, email, created_at."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id, email, created_at;",
            (email.lower().strip(), hashed_password)
        )
        row = cur.fetchone()
    conn.commit()
    conn.close()
    return {"id": row[0], "email": row[1], "created_at": str(row[2])}

def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieves a user by email."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, hashed_password, created_at FROM users WHERE email = %s;",
            (email.lower().strip(),)
        )
        row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "hashed_password": row[2], "created_at": str(row[3])}
    return None

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Retrieves a user by id."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, hashed_password, created_at FROM users WHERE id = %s;",
            (user_id,)
        )
        row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "hashed_password": row[2], "created_at": str(row[3])}
    return None

def get_document(document_id: int) -> Optional[dict]:
    """Retrieves document metadata including owner user_id."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, filename, uploaded_at, doc_type, user_id FROM documents WHERE id = %s;",
            (document_id,)
        )
        row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "filename": row[1],
            "uploaded_at": str(row[2]),
            "doc_type": row[3],
            "user_id": row[4],
        }
    return None

def save_document(filename: str, doc_type: str, user_id: Optional[int] = None) -> int:
    """Inserts a row into documents, returns its id."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO documents (filename, doc_type, user_id) VALUES (%s, %s, %s) RETURNING id;",
            (filename, doc_type, user_id)
        )
        doc_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return doc_id

def save_report(document_id: int, report_data: dict) -> None:
    """Inserts a row into reports with the report as JSONB."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO reports (document_id, report_json) VALUES (%s, %s);",
            (document_id, json.dumps(report_data))
        )
    conn.commit()
    conn.close()

def get_report(document_id: int) -> Optional[dict]:
    """Retrieves the most recent report for a document."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT report_json FROM reports WHERE document_id = %s ORDER BY created_at DESC LIMIT 1;",
            (document_id,)
        )
        row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_all_chunks(exclude_document_id: Optional[int] = None) -> List[str]:
    """Returns the text of all stored chunks, optionally excluding one document.
    
    Used to build the MinHash / LSH exact-match index from the existing
    source corpus so the index is not empty when scanning a new document.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        if exclude_document_id is not None:
            cur.execute(
                """
                SELECT c.text 
                FROM chunks c 
                JOIN documents d ON c.document_id = d.id 
                WHERE c.document_id != %s AND d.doc_type = 'source' 
                ORDER BY c.id;
                """,
                (exclude_document_id,)
            )
        else:
            cur.execute(
                """
                SELECT c.text 
                FROM chunks c 
                JOIN documents d ON c.document_id = d.id 
                WHERE d.doc_type = 'source' 
                ORDER BY c.id;
                """
            )
        rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]
