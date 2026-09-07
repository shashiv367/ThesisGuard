import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.keyword_service import extract_keywords

def run_tests():
    sample_text = (
        "Plagiarism detection systems have historically relied on exact string matching "
        "and n-gram overlap, which are easily defeated by paraphrasing. To counter this, "
        "modern systems utilize dense sentence embeddings and semantic similarity metrics "
        "like cosine similarity to catch reworded plagiarism. These deep learning approaches "
        "encode the fundamental meaning of a sentence into a vector space, allowing for "
        "highly accurate retrieval."
    )
    
    print("Extracting keywords using KeyBERT (this will load the shared SBERT model)...")
    print("-" * 50)
    print(f"Sample Text:\n{sample_text}\n")
    
    keywords = extract_keywords(sample_text, top_n=10)
    
    print("Top Keywords & Keyphrases (with confidence scores):")
    for kw, score in keywords:
        print(f" - {kw}: {score:.4f}")
        
    print("-" * 50)

if __name__ == "__main__":
    run_tests()
