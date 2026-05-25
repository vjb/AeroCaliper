import csv
import json
import google.genai
import os
from evaluators import evaluate_finops_compliance, evaluate_hr_compliance

def run_empirical_backtest(candidate_prompt: str, domain: str) -> str:
    """
    Run the empirical backtest against the golden dataset using the candidate system prompt.
    Returns the results of the evaluation, including any failed test cases.
    """
    # Load dataset
    try:
        with open("golden_dataset.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            test_cases = list(reader)
    except FileNotFoundError:
        return "FAIL: golden_dataset.csv not found."

    filtered_cases = []
    
    # Filter the dataset based on the active policy domain
    for row in test_cases:
        is_hr_case = any(x in row.get("evaluation_detail", "").lower() or x in row.get("llm.user_prompt", "").lower() for x in ["pii", "salary", "contractor", "draft", "payroll", "offer letter", "health", "hr"])
        if (domain == "hr" and not is_hr_case) or (domain == "finops" and is_hr_case):
            continue
        filtered_cases.append(row)

    if not filtered_cases:
        return "FAIL: No test cases matched the domain."

    passed_cases = 0
    failed_cases_info = []

    client = google.genai.Client(vertexai=True, api_key=os.environ.get("GOOGLE_AGENT_PLATFORM_API_KEY"))

    for idx, row in enumerate(filtered_cases, 1):
        test_request = f"System Instructions: {candidate_prompt}\n\nUser Request: {row['llm.user_prompt']}\n\nReturn ONLY valid JSON."
        
        try:
            response = client.models.generate_content(
                model="gemini-3.1-pro-preview",
                contents=test_request,
            )
            simulation_output = response.text.strip()
            
            cleaned_output = simulation_output.replace("```json", "").replace("```", "").strip()
            payload = json.loads(cleaned_output)
            
            if domain == "hr":
                res = evaluate_hr_compliance(payload)
            else:
                res = evaluate_finops_compliance(payload)
                
            if res.startswith("PASSED"):
                passed_cases += 1
            else:
                failed_cases_info.append({
                    "user_prompt": row['llm.user_prompt'],
                    "verdict": res,
                    "output": simulation_output
                })
        except Exception as e:
            failed_cases_info.append({
                "user_prompt": row['llm.user_prompt'],
                "verdict": f"Simulation parse/run error: {e}",
                "output": "No valid JSON output"
            })
            
    pass_rate = (passed_cases / len(filtered_cases)) * 100 if filtered_cases else 0
    
    if pass_rate == 100:
        return f"SUCCESS: 100% PASS ({passed_cases}/{len(filtered_cases)} cases). The prompt is fully compliant."
    else:
        return f"FAIL: {pass_rate:.0f}% PASS ({passed_cases}/{len(filtered_cases)} cases). The candidate prompt failed the following cases:\n" + json.dumps(failed_cases_info, indent=2)
