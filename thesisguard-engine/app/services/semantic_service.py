from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values
from app.services.db_service import get_connection

# Load the SBERT model globally so it's loaded only once in memory
# and can be shared by other modules (like keyword_service)
model = SentenceTransformer("all-MiniLM-L6-v2")


def batch_encode(chunks: list[str]):
    """Encodes a list of text chunks in a single batched call.
    
    Returns a list of numpy arrays (one embedding per chunk).
    This is significantly faster than encoding one chunk at a time
    because SentenceTransformer can parallelise internally.
    """
    if not chunks:
        return []
    return model.encode(chunks)


def index_source_document(document_id: int, chunks: list[str]) -> None:
    """Encodes chunks and saves them with embeddings to PostgreSQL using pgvector."""
    if not chunks:
        return
        
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


def semantic_search(
    query_chunk: str,
    top_k: int = 3,
    precomputed_embedding=None,
    conn=None,
    exclude_document_id: int = None,
) -> list[dict]:
    """Performs cosine similarity search against pgvector.
    
    Args:
        query_chunk: The text chunk to search for (used only if precomputed_embedding is None).
        top_k: Number of top results to return.
        precomputed_embedding: Pre-computed embedding vector (list of floats). 
            If provided, skips the expensive model.encode() call.
        conn: An existing psycopg2 connection to reuse.
            If None, a new connection is opened and closed automatically.
        exclude_document_id: If provided, excludes chunks belonging to this
            document from results (prevents a document matching itself).
    """
    # Use pre-computed embedding if available, otherwise encode on the fly
    if precomputed_embedding is not None:
        q_embedding = precomputed_embedding
    else:
        q_embedding = model.encode([query_chunk])[0].tolist()

    # Ensure it's a plain list (not a numpy array) for psycopg2
    if hasattr(q_embedding, 'tolist'):
        q_embedding = q_embedding.tolist()

    # Manage connection lifecycle
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection()

    results = []
    try:
        with conn.cursor() as cur:
            if exclude_document_id is not None:
                # Exclude the uploaded document's own chunks and only search 'source' corpus
                cur.execute(
                    """
                    SELECT c.id, c.document_id, c.chunk_index, c.text, 1 - (c.embedding <=> %s::vector) AS similarity
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.document_id != %s AND d.doc_type = 'source'
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (q_embedding, exclude_document_id, q_embedding, top_k)
                )
            else:
                # Original behaviour — search all source chunks
                cur.execute(
                    """
                    SELECT c.id, c.document_id, c.chunk_index, c.text, 1 - (c.embedding <=> %s::vector) AS similarity
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.doc_type = 'source'
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (q_embedding, q_embedding, top_k)
                )
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "chunk_id": row[0],
                    "document_id": row[1],
                    "chunk_index": row[2],
                    "text": row[3],
                    "similarity": row[4]
                })
    finally:
        if owns_connection:
            conn.close()

    return results
