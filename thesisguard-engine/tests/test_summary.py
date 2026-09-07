import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.summary_service import summarize_source

def run_tests():
    sample_text = (
        "Plagiarism is the representation of another author's language, thoughts, ideas, or expressions as one's own original work. "
        "In educational contexts, there are differing definitions of plagiarism depending on the institution. Plagiarism is considered "
        "a violation of academic integrity and a breach of journalistic ethics. It is subject to sanctions such as penalties, suspension, "
        "expulsion from school or work, substantial fines and even incarceration. "
        "Recently, cases of 'extreme plagiarism' have been identified in academia. The modern concept of plagiarism as immoral and "
        "originality as an ideal emerged in Europe in the 18th century, particularly with the Romantic movement. "
        "Plagiarism is not in itself a crime, but like counterfeiting fraud can be punished in a court for prejudices caused by copyright infringement, "
        "violation of moral rights, or torts. In academia and industry, it is a serious ethical offense. Plagiarism and copyright infringement "
        "overlap to a considerable extent, but they are not equivalent concepts, and many types of plagiarism do not constitute copyright infringement, "
        "which is defined by copyright law and may be adjudicated by courts."
    )
    
    print("Generating Summary using DistilBART (this will download model weights on first run)...")
    print("-" * 50)
    print(f"Original Text (Length: {len(sample_text)} chars):\n{sample_text}\n")
    print("-" * 50)
    
    summary = summarize_source(sample_text, max_length=60, min_length=20)
    
    print(f"Generated Summary (Length: {len(summary)} chars):\n{summary}")
    print("-" * 50)

if __name__ == "__main__":
    run_tests()
