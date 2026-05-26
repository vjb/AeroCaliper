import os
import pandas as pd
import pytest

def test_golden_dataset_integrity():
    """
    TDD Assertion:
    - golden_dataset.csv exists
    - contains >= 40 rows
    - columns contain no nulls
    - covers both 'hr' and 'finops' use cases
    """
    csv_path = "golden_dataset.csv"
    assert os.path.exists(csv_path), "golden_dataset.csv must exist in the root."
    
    df = pd.read_csv(csv_path)
    
    # Assert row count
    assert len(df) >= 40, f"Expected at least 40 rows, got {len(df)}."
    
    # Assert expected columns
    expected_cols = [
        "prompt_id",
        "use_case",
        "input_text",
        "expected_behavior",
        "is_malicious_injection",
        "human_expert_label"
    ]
    assert list(df.columns) == expected_cols, f"Expected columns {expected_cols}, got {list(df.columns)}."
    
    # Assert no null values
    assert df.isnull().sum().sum() == 0, "Dataset contains null values."
    
    # Assert both use cases covered
    use_cases = df["use_case"].unique()
    assert "hr" in use_cases, "Dataset must cover 'hr' use case."
    assert "finops" in use_cases, "Dataset must cover 'finops' use case."
