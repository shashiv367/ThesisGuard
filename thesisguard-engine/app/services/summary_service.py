import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Load and cache the summarizer at the module level
# We use DistilBART for a good balance of speed (CPU) and abstractive quality
tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6", token=HF_TOKEN)
model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6", token=HF_TOKEN)

# In-memory cache: avoids re-summarizing the same source text within a session.
# Key = first 200 chars of input text (enough to deduplicate matching chunks).
_summary_cache: dict[str, str] = {}

def summarize_source(text: str, max_length: int = 60, min_length: int = 20) -> str:
    """Generates an abstractive summary of the source document.
    
    Results are cached so that repeated calls with the same source text
    (common when multiple query chunks match the same source chunk)
    return instantly instead of running beam search again.
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    # Check cache first — avoids redundant DistilBART calls
    cache_key = text[:200]
    if cache_key in _summary_cache:
        return _summary_cache[cache_key]
        
    # Truncate long documents to avoid exceeding the model's token limits
    truncated = text[:3000]
    
    # Generate summary — num_beams=2 is ~2x faster than 4 on CPU
    # with minimal quality loss for short source chunks
    inputs = tokenizer(truncated, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(
        inputs["input_ids"], 
        max_length=max_length, 
        min_length=min_length, 
        length_penalty=2.0, 
        num_beams=2, 
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    # Store in cache for subsequent calls
    _summary_cache[cache_key] = summary
    return summary
