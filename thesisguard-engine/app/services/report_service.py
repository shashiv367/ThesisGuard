from app.services.exact_match_service import check_exact_match
from app.services.semantic_service import semantic_search, batch_encode
from app.services.keyword_service import extract_keywords
from app.services.summary_service import summarize_source
from app.services.ai_detection_service import detect_ai_generated_batch
from app.services.db_service import get_connection

def generate_report(query_chunks: list[str], lsh, minhashes, document_id: int = None) -> list[dict]:
    report = []
    
    # ── Performance optimisation ──────────────────────────────────
    # 1. Batch-encode ALL query chunks in one call instead of
    #    encoding one-by-one inside the loop.
    embeddings = batch_encode(query_chunks)
    
    # 2. Third detection layer: classify all query chunks for AI-generated text
    ai_detections = detect_ai_generated_batch(query_chunks)
    
    # 3. Open a single DB connection to reuse for every semantic
    #    search instead of opening/closing one per chunk.
    conn = get_connection()
    
    try:
        for i, chunk in enumerate(query_chunks):
            # Layer 1: Check Exact Match
            exact_matches = check_exact_match(chunk, lsh, minhashes) if lsh and minhashes else []
            
            # Layer 2: Check Semantic Match — use pre-computed embedding + shared connection.
            # Also exclude the current document's own chunks so it doesn't match itself.
            precomputed = embeddings[i].tolist() if len(embeddings) > 0 else None
            semantic_matches = semantic_search(
                chunk,
                top_k=3,
                precomputed_embedding=precomputed,
                conn=conn,
                exclude_document_id=document_id,
            )
            
            # Log the top similarity score for each chunk (helps with threshold tuning)
            top_score = semantic_matches[0]['similarity'] if semantic_matches else 0.0
            print(f"  Chunk {i}: top_similarity={top_score:.4f} | exact_matches={len(exact_matches)} | text={chunk[:60]}...")
            
            # Filter semantic matches by threshold.
            # 0.60 catches paraphrased content; tune on PAN-PC-11 for production.
            valid_semantic = [m for m in semantic_matches if m['similarity'] >= 0.60]
            
            if exact_matches:
                match_type = "exact"
            elif valid_semantic:
                match_type = "semantic"
            else:
                match_type = "none"
                
            # Layer 3: AI-generated text analysis
            ai_info = ai_detections[i] if i < len(ai_detections) else {
                "label": "human",
                "confidence": 0.0,
                "formatted": "Likely human (0% confidence)"
            }
            
            chunk_report = {
                "chunk_index": i,
                "text": chunk,
                "match_type": match_type,
                "exact_match_ids": exact_matches,
                "semantic_matches": valid_semantic,
                "ai_detection": ai_info,
            }
            
            # Attach keyword tags and source summaries where a match exists
            if match_type != "none":
                # Extract keywords for the plagiarized chunk to tag the topic
                chunk_report["keyword_tags"] = [
                    {"keyword": kw, "score": float(score)} 
                    for kw, score in extract_keywords(chunk, top_n=3)
                ]
                
                # Generate a summary of the matched source text 
                # We summarize the top semantic match's text as a representative source
                if valid_semantic:
                    top_match_text = valid_semantic[0]["text"]
                    chunk_report["source_summary"] = summarize_source(top_match_text)
                
            report.append(chunk_report)
    finally:
        conn.close()
        
    return report
