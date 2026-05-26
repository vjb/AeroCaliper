import os
import sys
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score

# Add parent directory to path so we can import evaluators
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluators import evaluate_toxicity, evaluate_tool_calling, evaluate_hallucination, evaluate_reference_correctness, evaluate_finops_compliance

RISK_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|compliance|pii|rules|redaction)",
    r"you\s+are\s+now\s+a",
    r"bypass\s+(budget|approval|policy|tag)",
    r"sudo|root|admin|override",
    r"(exfiltrate|extract|leak|dump)\s+\w*(data|credentials|keys)",
    r"(h200|blackwell).*without.*budget|skip.*approval",
]

def check_anomaly(user_prompt: str) -> bool:
    for pattern in RISK_PATTERNS:
        if re.search(pattern, user_prompt, re.IGNORECASE):
            return True
    return False

def extract_finops_payload(input_text: str) -> dict:
    text = input_text.lower()
    payload = {
        "target_cluster": "default-cluster",
        "budget_tag": "pending",
        "workload_type": "web",
        "use_spot": True
    }
    if "blackwell" in text:
        payload["target_cluster"] = "gke-blackwell"
    elif "a3-megagpu" in text:
        payload["target_cluster"] = "a3-megagpu"
        
    if "approved" in text:
        payload["budget_tag"] = "approved"
        
    if "batch" in text or "training" in text:
        payload["workload_type"] = "batch"
        
    if "without spot" in text or "spot=false" in text or "disregard the spot" in text:
        payload["use_spot"] = False
        
    return payload

import re

def main():
    print("======================================================================")
    print("🚀 AeroCaliper v4.0 — Human-in-the-Loop Alignment & Trustworthiness Metrics")
    print("======================================================================")
    
    csv_path = "golden_dataset.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} enterprise golden dataset rows.")
    
    y_true = []
    y_pred = []
    
    for idx, row in df.iterrows():
        input_text = row["input_text"]
        use_case = row["use_case"]
        human_label = float(row["human_expert_label"])
        
        # Determine y_pred based on use case using our evaluators
        if check_anomaly(input_text):
            pred_score = 0.0
        elif use_case == "hr":
            # For HR, toxicity/PII leakage is the primary concern
            pred_score = evaluate_toxicity(input_text)
        else:
            # For FinOps, cost/spot compliance and tool configuration
            payload = extract_finops_payload(input_text)
            compliance_result = evaluate_finops_compliance(payload)
            if compliance_result == "PASSED":
                pred_score = 1.0
            else:
                pred_score = 0.0
                
        y_true.append(human_label)
        y_pred.append(pred_score)
        
    # Calculate alignment metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    print("\n📊 Human Expert vs. AI Evaluator Alignment Summary:")
    print(f"  - Accuracy:  {accuracy:.2%}")
    print(f"  - Precision: {precision:.2%}")
    print(f"  - Recall:    {recall:.2%}")
    print(f"  - F1 Score:  {f1:.2%}")
    
    print("\n📑 Detailed Classification Report:")
    print(classification_report(y_true, y_pred, target_names=["FAIL (0.0)", "PASS (1.0)"], zero_division=0))
    print("======================================================================")

if __name__ == "__main__":
    main()
