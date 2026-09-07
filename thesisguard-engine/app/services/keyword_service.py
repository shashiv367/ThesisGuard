from keybert import KeyBERT
from app.services.semantic_service import model

# Initialize KeyBERT with the shared SentenceTransformer model
kw_model = KeyBERT(model=model)

def extract_keywords(text: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Extracts keywords from text using KeyBERT and the shared SBERT model."""
    return kw_model.extract_keywords(
        text, 
        keyphrase_ngram_range=(1, 2),
        stop_words="english", 
        top_n=top_n
    )
