import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.exact_match_service import build_exact_match_index, check_exact_match

def run_tests():
    print("Building Index from source corpus...")
    source_chunks = [
        "This is the first sentence of our sample text. It provides some basic context.",
        "The quick brown fox jumps over the lazy dog.",
        "Plagiarism detection engines often use n-gram shingling to catch verbatim copying.",
        "In the final analysis, the results were inconclusive but promising."
    ]
    
    # We use a threshold of 0.5 (meaning roughly 50% of the 5-grams must match)
    lsh, minhashes = build_exact_match_index(source_chunks, threshold=0.5)
    
    queries = {
        "Verbatim Copy": "Plagiarism detection engines often use n-gram shingling to catch verbatim copying.",
        "Lightly Edited Copy": "Plagiarism detection systems frequently use n-gram shingling to catch verbatim copying.",
        "Unrelated Sentence": "Machine learning models require a lot of data to train effectively."
    }
    
    print("-" * 50)
    for name, text in queries.items():
        print(f"Testing {name}:")
        print(f"Query Text: '{text}'")
        
        matches = check_exact_match(text, lsh, minhashes)
        
        if matches:
            print(f"-> FLAGGED! Matches found at source indices: {matches}")
            for m in matches:
                print(f"   Matched Source: '{source_chunks[m]}'")
        else:
            print("-> CLEAN. No exact matches found.")
        print("-" * 50)

if __name__ == "__main__":
    run_tests()
