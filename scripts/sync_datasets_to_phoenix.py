import pandas as pd
from phoenix.client import Client
import os
from dotenv import load_dotenv

def sync_datasets():
    load_dotenv()
    print("Syncing golden_dataset.csv to Phoenix Datasets...")
    client = Client()
    
    # Load the CSV
    try:
        df = pd.read_csv("golden_dataset.csv")
    except Exception as e:
        print(f"Error reading golden_dataset.csv: {e}")
        return

    # Dynamically support both old and new schemas
    if "input_text" in df.columns:
        df["llm.user_prompt"] = df["input_text"]
    if "use_case" in df.columns:
        df["domain"] = df["use_case"]
    else:
        # Split into finops and hr datasets for cleaner organization in Phoenix
        finops_keywords = ["cluster", "batch", "gpu", "kubernetes"]
        hr_keywords = ["pii", "salary", "contractor", "draft", "payroll", "offer letter", "health", "hr"]
        
        def determine_domain(prompt):
            prompt = str(prompt).lower()
            if any(kw in prompt for kw in hr_keywords):
                return "hr"
            return "finops"
            
        df["domain"] = df["llm.user_prompt"].apply(determine_domain)

    # Ensure evaluation columns exist
    if "evaluation_result" not in df.columns:
        if "expected_compliance_flag" in df.columns:
            # Map expected_compliance_flag (True means passed/compliant, False means failed/violating)
            df["evaluation_result"] = df["expected_compliance_flag"].apply(lambda x: "PASSED" if str(x).lower() in ("true", "1", "passed", "compliant") else "FAILED")
        else:
            df["evaluation_result"] = "PASSED"

    if "evaluation_detail" not in df.columns:
        df["evaluation_detail"] = df["domain"] + " compliance check"

    if "trace_id" not in df.columns:
        df["trace_id"] = df["prompt_id"] if "prompt_id" in df.columns else "trace-" + df.index.astype(str)

    if "span_id" not in df.columns:
        df["span_id"] = "span-" + df.index.astype(str)
        
    finops_df = df[df["domain"] == "finops"].copy()
    hr_df = df[df["domain"] == "hr"].copy()
    
    # Sync FinOps Dataset
    print(f"Creating 'AeroCaliper FinOps Golden' dataset with {len(finops_df)} examples...")
    client.datasets.create_dataset(
        name="AeroCaliper FinOps Golden",
        dataframe=finops_df,
        input_keys=["llm.user_prompt"],
        output_keys=["evaluation_result", "evaluation_detail"],
        metadata_keys=["trace_id", "span_id"]
    )
    
    # Sync HR Dataset
    print(f"Creating 'AeroCaliper HR Golden' dataset with {len(hr_df)} examples...")
    client.datasets.create_dataset(
        name="AeroCaliper HR Golden",
        dataframe=hr_df,
        input_keys=["llm.user_prompt"],
        output_keys=["evaluation_result", "evaluation_detail"],
        metadata_keys=["trace_id", "span_id"]
    )
    
    print("Successfully synced datasets to Phoenix Cloud!")

if __name__ == "__main__":
    sync_datasets()
