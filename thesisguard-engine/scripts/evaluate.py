import os
import sys
import json
import csv
import argparse
import numpy as np

# Set headless backend for matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add project root to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.extraction_service import chunk_text
from app.services.db_service import save_document
from app.services.semantic_service import index_source_document, semantic_search
from app.services.exact_match_service import build_exact_match_index, check_exact_match

def load_and_prepare_dataset(base_dir: str = "pan_data"):
    """Loads source and suspicious documents, indexing the source corpus into pgvector and LSH."""
    print("--- 1. Loading Ground Truth and Indexing Source Corpus ---")
    gt_path = os.path.join(base_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Dataset not found at {gt_path}. Please run generate_mock_dataset.py first.")
        
    with open(gt_path, "r") as f:
        ground_truth = json.load(f)
        
    src_dir = os.path.join(base_dir, "src")
    all_source_chunks = []
    
    for fname in sorted(os.listdir(src_dir)):
        with open(os.path.join(src_dir, fname), "r") as f:
            text = f.read()
            chunks = chunk_text(text)
            all_source_chunks.extend(chunks)
            
            # Save and index into PostgreSQL
            doc_id = save_document(f"EVAL_SRC_{fname}", "source")
            index_source_document(doc_id, chunks)
            
    # Build exact-match LSH index
    lsh, minhashes = build_exact_match_index(all_source_chunks, threshold=0.5)
    
    # Process suspicious documents and precompute matches
    print("--- 2. Scanning Suspicious Documents and Precomputing Matches ---")
    susp_dir = os.path.join(base_dir, "susp")
    evaluated_chunks = []
    
    for fname in sorted(os.listdir(susp_dir)):
        with open(os.path.join(susp_dir, fname), "r") as f:
            text = f.read()
            chunks = chunk_text(text)
            
        gt_spans = ground_truth.get(fname, [])
        
        for chunk in chunks:
            # Ground truth determination
            is_actual_plagiarism = any(gt_span in chunk or chunk in gt_span for gt_span in gt_spans)
            
            # Exact match prediction
            exact_matches = check_exact_match(chunk, lsh, minhashes)
            is_pred_exact = len(exact_matches) > 0
            
            # Semantic search matches
            semantic_matches = semantic_search(chunk, top_k=3)
            top_similarity = max([m["similarity"] for m in semantic_matches], default=0.0)
            
            evaluated_chunks.append({
                "chunk": chunk,
                "is_actual": is_actual_plagiarism,
                "is_pred_exact": is_pred_exact,
                "top_similarity": top_similarity,
            })
            
    print(f"Total evaluated chunks: {len(evaluated_chunks)}")
    return evaluated_chunks

def compute_metrics(tp: int, fp: int, fn: int):
    """Calculates precision, recall, and F1 score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def run_threshold_sweep(evaluated_chunks: list, prod_threshold: float = 0.60, results_dir: str = "results"):
    """Sweeps similarity thresholds from 0.50 to 0.95 and plots the Precision-Recall curve."""
    print("\n" + "=" * 50)
    print(">>> MODE: PRECISION-RECALL CURVE THRESHOLD SWEEP <<<")
    print("=" * 50)
    os.makedirs(results_dir, exist_ok=True)
    
    thresholds = [round(t, 2) for t in np.arange(0.50, 0.96, 0.05)]
    precisions = []
    recalls = []
    f1s = []
    
    print(f"{'Threshold':>10} | {'Precision':>10} | {'Recall':>10} | {'F1 Score':>10} | {'TP':>4} | {'FP':>4} | {'FN':>4}")
    print("-" * 65)
    
    for t in thresholds:
        tp = fp = fn = 0
        for item in evaluated_chunks:
            is_pred = item["top_similarity"] >= t
            actual = item["is_actual"]
            
            if is_pred and actual:
                tp += 1
            elif is_pred and not actual:
                fp += 1
            elif not is_pred and actual:
                fn += 1
                
        p, r, f1 = compute_metrics(tp, fp, fn)
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)
        print(f"{t:>10.2f} | {p:>10.2f} | {r:>10.2f} | {f1:>10.2f} | {tp:>4} | {fp:>4} | {fn:>4}")
        
    # Plotting Precision-Recall Curve
    plt.figure(figsize=(9, 6.5))
    plt.plot(recalls, precisions, color="#2563eb", marker="o", linewidth=2.2, label="Semantic Layer PR Curve")
    
    # Group threshold values by (r, p) point to avoid overlapping text annotations
    point_thresholds = {}
    for p, r, t in zip(precisions, recalls, thresholds):
        key = (round(r, 4), round(p, 4))
        if key not in point_thresholds:
            point_thresholds[key] = []
        point_thresholds[key].append(t)
        
    for (r, p), t_list in point_thresholds.items():
        if len(t_list) == 1:
            label_text = f"t={t_list[0]:.2f}"
        elif len(t_list) <= 2:
            label_text = f"t={', '.join(f'{x:.2f}' for x in t_list)}"
        else:
            label_text = f"t={min(t_list):.2f}..{max(t_list):.2f}"
            
        y_offset = -18 if p > 0.8 else 8
        x_offset = -35 if r > 0.8 else 8
        plt.annotate(
            label_text,
            (r, p),
            textcoords="offset points",
            xytext=(x_offset, y_offset),
            fontsize=8.5,
            color="#0f172a",
            fontweight="600",
            bbox=dict(boxstyle="round,pad=0.25", fc="#f8fafc", ec="#94a3b8", alpha=0.9)
        )
        
    # Highlight current production threshold
    prod_t = round(prod_threshold, 2)
    if prod_t in thresholds:
        idx = thresholds.index(prod_t)
        prod_p = precisions[idx]
        prod_r = recalls[idx]
    else:
        # Compute explicitly if custom threshold
        tp = fp = fn = 0
        for item in evaluated_chunks:
            is_pred = item["top_similarity"] >= prod_t
            if is_pred and item["is_actual"]: tp += 1
            elif is_pred and not item["is_actual"]: fp += 1
            elif not is_pred and item["is_actual"]: fn += 1
        prod_p, prod_r, _ = compute_metrics(tp, fp, fn)
        
    plt.plot(
        prod_r,
        prod_p,
        marker="*",
        markersize=16,
        color="#dc2626",
        markeredgecolor="#991b1b",
        markeredgewidth=1.5,
        linestyle="None",
        label=f"Production Threshold (t={prod_threshold:.2f}, P={prod_p:.2f}, R={prod_r:.2f})"
    )
    
    plt.title("Precision-Recall Curve (Semantic Similarity Threshold Sweep)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Recall", fontsize=11, fontweight="600")
    plt.ylabel("Precision", fontsize=11, fontweight="600")
    plt.xlim(-0.05, 1.08)
    plt.ylim(-0.05, 1.08)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="lower left", fontsize=10, frameon=True)
    
    curve_path = os.path.join(results_dir, "precision_recall_curve.png")
    plt.savefig(curve_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"\n[OK] Precision-Recall curve saved to: {curve_path}")

def run_ablation_study(evaluated_chunks: list, threshold: float = 0.60, results_dir: str = "results"):
    """Runs ablation study comparing Exact-only, Semantic-only, and Combined pipeline."""
    print("\n" + "=" * 50)
    print(f">>> MODE: ABLATION STUDY (Semantic Threshold: {threshold:.2f}) <<<")
    print("=" * 50)
    os.makedirs(results_dir, exist_ok=True)
    
    configs = [
        {"name": "Exact-Match Only", "key": "exact"},
        {"name": "Semantic Layer Only", "key": "semantic"},
        {"name": "Combined Pipeline", "key": "combined"},
    ]
    
    results = []
    
    for cfg in configs:
        tp = fp = fn = 0
        for item in evaluated_chunks:
            if cfg["key"] == "exact":
                is_pred = item["is_pred_exact"]
            elif cfg["key"] == "semantic":
                is_pred = item["top_similarity"] >= threshold
            else: # combined
                is_pred = item["is_pred_exact"] or (item["top_similarity"] >= threshold)
                
            actual = item["is_actual"]
            if is_pred and actual:
                tp += 1
            elif is_pred and not actual:
                fp += 1
            elif not is_pred and actual:
                fn += 1
                
        p, r, f1 = compute_metrics(tp, fp, fn)
        results.append({
            "Configuration": cfg["name"],
            "Precision": round(p, 4),
            "Recall": round(r, 4),
            "F1": round(f1, 4),
            "TP": tp,
            "FP": fp,
            "FN": fn,
        })
        
    # 1. Print Comparison Table to Console
    print(f"\n{'Configuration':<25} | {'Precision':>10} | {'Recall':>10} | {'F1 Score':>10} | {'TP':>4} | {'FP':>4} | {'FN':>4}")
    print("-" * 75)
    for res in results:
        print(f"{res['Configuration']:<25} | {res['Precision']:>10.2f} | {res['Recall']:>10.2f} | {res['F1']:>10.2f} | {res['TP']:>4} | {res['FP']:>4} | {res['FN']:>4}")
        
    # 2. Save CSV
    csv_path = os.path.join(results_dir, "ablation_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Configuration", "Precision", "Recall", "F1", "TP", "FP", "FN"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] Ablation comparison table saved to: {csv_path}")
    
    # 3. Save Grouped / Side-by-Side Bar Chart showing F1 for all three configurations
    fig, ax = plt.subplots(figsize=(9, 6))
    cfg_names = [r["Configuration"] for r in results]
    f1_values = [r["F1"] for r in results]
    precision_values = [r["Precision"] for r in results]
    recall_values = [r["Recall"] for r in results]
    
    x = np.arange(len(cfg_names))
    width = 0.25
    
    rects1 = ax.bar(x - width, precision_values, width, label='Precision', color='#3b82f6')
    rects2 = ax.bar(x, recall_values, width, label='Recall', color='#10b981')
    rects3 = ax.bar(x + width, f1_values, width, label='F1 Score', color='#8b5cf6')
    
    ax.set_ylabel('Score', fontsize=11, fontweight="600")
    ax.set_title(f'Ablation Study: Detection Layer Performance Comparison (Threshold={threshold:.2f})', fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(cfg_names, fontsize=10, fontweight="600")
    ax.set_ylim(0, 1.2)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', fontsize=10)
    
    # Add value labels above bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight="bold")
                        
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    
    chart_path = os.path.join(results_dir, "ablation_comparison.png")
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[OK] Ablation comparison bar chart saved to: {chart_path}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate ThesisGuard against PAN Corpus (Threshold Sweep & Ablation)")
    parser.add_argument(
        "--mode",
        choices=["curve", "ablation", "full"],
        default="full",
        help="Evaluation mode: 'curve' (threshold sweep PR curve), 'ablation' (layer comparison), or 'full' (both)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Semantic similarity threshold for production/ablation (default: 0.60)"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory to save output plots and CSV (default: results)"
    )
    args = parser.parse_args()
    
    evaluated_chunks = load_and_prepare_dataset()
    
    if args.mode in ["curve", "full"]:
        run_threshold_sweep(evaluated_chunks, prod_threshold=args.threshold, results_dir=args.results_dir)
        
    if args.mode in ["ablation", "full"]:
        run_ablation_study(evaluated_chunks, threshold=args.threshold, results_dir=args.results_dir)
        
    print("\n>>> EVALUATION COMPLETE! <<<")

if __name__ == "__main__":
    main()
