import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from transformers import pipeline

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# ==============================================================================
# NOTE ON HIGHER-ACCURACY MODEL ALTERNATIVES FOR PROJECT REPORT:
#
# "desklib/ai-text-detector-v1.01" (based on DeBERTa-v3-large) is currently
# leading the RAID (Robust AI Detection) benchmark. It offers state-of-the-art
# discrimination accuracy and significantly reduced false-positive rates on
# adversarial attacks, paraphrased machine output, and mixed-author texts.
#
# However, it is a substantially larger model (~1.74 GB weights, high GPU/RAM
# overhead and latency), representing a deliberate speed/memory vs. accuracy
# tradeoff if swapped in.
#
# Here, "ahmediqbal/ai-text-detector-model" (DistilBERT-based, ~268 MB) is used
# as the default lightweight, high-throughput model suitable for local deployment.
# ==============================================================================

# Lazy singleton instance for the classifier pipeline
_ai_classifier = None

def get_ai_classifier():
    """Lazily loads the AI text classifier pipeline only on first use.
    
    This ensures the model does not sit in memory alongside the SentenceTransformer
    and KeyBERT summarization models unless AI text detection is actually invoked.
    """
    global _ai_classifier
    if _ai_classifier is None:
        _ai_classifier = pipeline(
            "text-classification",
            model="ahmediqbal/ai-text-detector-model",
            truncation=True,
            max_length=512,
            token=HF_TOKEN,
        )
    return _ai_classifier

def _format_prediction(raw_label: str, score: float) -> Dict[str, Any]:
    """Formats raw model output into probabilistic confidence report.
    
    Never outputs a flat yes/no, and is never used to auto-reject submissions,
    as AI detection is inherently a probabilistic signal with a known false-positive rate.
    """
    confidence = round(float(score), 4)
    
    # Model id2label: {0: 'Human', 1: 'AI'}
    if str(raw_label).upper() in ["AI", "LABEL_1", "1"]:
        # AI detection models are notoriously overconfident on formal academic writing.
        # To reduce false positives on human-written scholarly text, we enforce an
        # extremely high confidence threshold before branding a chunk as "Likely AI-generated".
        if confidence >= 0.9995:
            label = "AI-generated"
            ai_score = confidence
            pct = int(round(confidence * 100))
            formatted = f"Likely AI-generated ({pct}% confidence)"
        else:
            # Reclassify as human due to false-positive mitigation
            label = "human"
            ai_score = round(1.0 - confidence, 4)
            # Cap the percentage so it doesn't look confusingly low
            pct = max(50, int(round(ai_score * 100)))
            formatted = f"Likely human ({pct}% confidence)"
    else:
        label = "human"
        ai_score = round(1.0 - confidence, 4)
        pct = int(round(confidence * 100))
        formatted = f"Likely human ({pct}% confidence)"
        
    return {
        "label": label,
        "confidence": confidence,
        "ai_score": ai_score,
        "formatted": formatted,
    }

def detect_ai_generated(text_chunk: str) -> Dict[str, Any]:
    """Analyzes a single text chunk for signals of AI-generated content.
    
    Returns:
        Dict with 'label' (human/AI-generated), 'confidence' (float),
        'ai_score' (float in [0, 1]), and 'formatted' (e.g. "Likely AI-generated (72% confidence)").
    """
    if not text_chunk or not text_chunk.strip():
        return {
            "label": "human",
            "confidence": 0.0,
            "ai_score": 0.0,
            "formatted": "Likely human (0% confidence)",
        }
        
    classifier = get_ai_classifier()
    predictions = classifier(text_chunk)
    pred = predictions[0] if predictions else {"label": "Human", "score": 0.5}
    return _format_prediction(pred["label"], pred["score"])

def detect_ai_generated_batch(text_chunks: List[str]) -> List[Dict[str, Any]]:
    """Batch processes multiple text chunks for optimal inference throughput."""
    if not text_chunks:
        return []
        
    # Replace empty strings with single space to prevent pipeline errors
    sanitized = [c if (c and c.strip()) else " " for c in text_chunks]
    
    classifier = get_ai_classifier()
    predictions = classifier(sanitized)
    
    results = []
    for pred in predictions:
        results.append(_format_prediction(pred["label"], pred["score"]))
    return results
