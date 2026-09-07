import os
import json

def create_dataset():
    base_dir = "pan_data"
    os.makedirs(os.path.join(base_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "susp"), exist_ok=True)
    
    # Fake Source Documents
    src1 = "Plagiarism detection engines often use n-gram shingling to catch verbatim copying. In the final analysis, the results were inconclusive but promising."
    src2 = "The quick brown fox jumps over the lazy dog. Artificial intelligence is transforming the modern world."
    
    with open(os.path.join(base_dir, "src", "src1.txt"), "w") as f: f.write(src1)
    with open(os.path.join(base_dir, "src", "src2.txt"), "w") as f: f.write(src2)
    
    # Fake Suspicious Documents
    # susp1 contains an exact copy of a sentence from src1
    susp1 = "Plagiarism detection engines often use n-gram shingling to catch verbatim copying. In the final analysis, the results were inconclusive but promising. This is a concluding sentence."
    # susp2 contains a semantic (paraphrased) copy of a sentence from src2
    susp2 = "We begin our study here. AI systems are radically changing our society today. We hope you enjoy the paper."
    # susp3 is totally original
    susp3 = "This is a completely original paper. It has no plagiarism whatsoever. We are very proud of it."
    
    with open(os.path.join(base_dir, "susp", "susp1.txt"), "w") as f: f.write(susp1)
    with open(os.path.join(base_dir, "susp", "susp2.txt"), "w") as f: f.write(susp2)
    with open(os.path.join(base_dir, "susp", "susp3.txt"), "w") as f: f.write(susp3)
    
    # Ground Truth Annotations mapping files to the plagiarized chunks
    ground_truth = {
        "susp1.txt": [
            "Plagiarism detection engines often use n-gram shingling to catch verbatim copying."
        ],
        "susp2.txt": [
            "AI systems are radically changing our society today."
        ]
    }
    
    with open(os.path.join(base_dir, "ground_truth.json"), "w") as f:
        json.dump(ground_truth, f, indent=4)
        
    print(f"Mock PAN dataset generated successfully in ./{base_dir}/")

if __name__ == "__main__":
    create_dataset()
