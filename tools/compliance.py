import os
from google.cloud import discoveryengine_v1
from tools.observability import trace_chain

@trace_chain(name="search_enterprise_policy")
def search_enterprise_policy(domain: str) -> str:


    """
    Query Vertex AI Search to fetch the relevant enterprise policy.
    Bypasses and falls back to local policies if GCP credentials or config are missing.
    """
    project_id = os.environ.get("GCP_PROJECT_ID")
    policy_bucket = os.environ.get("GCP_POLICY_BUCKET")
    
    if not project_id or not policy_bucket:
        return _read_local_policy(domain)
        
    location = "global"
    
    # Select the right datastore and engine based on the domain
    if domain == "finops":
        data_store_id = "aerocaliper-rag"
        engine_id = os.environ.get("VERTEX_AI_DATASTORE_ID", "aerocaliper-rag_1714421160000")
        query = "What are the restrictions on Blackwell, H200, and Spot instances?"
    elif domain == "hr":
        data_store_id = "aerocaliper-hr-rag"
        engine_id = os.environ.get("VERTEX_HR_DATASTORE_ID", "aerocaliper-hr-rag")
        query = "What are the rules regarding unredacted compensation, base salary, and PII in draft documents?"
    else:
        raise ValueError(f"Unknown domain: {domain}")

    try:
        client = discoveryengine_v1.SearchServiceClient(transport="rest")
        
        if engine_id:
            serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
        else:
            serving_config = client.serving_config_path(project_id, location, data_store_id, "default_config")
        
        request = discoveryengine_v1.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=1,
        )
        response = client.search(request)
        snippets = []
        for result in response.results:
            data = result.document.struct_data
            if data and "content" in data:
                snippets.append(data["content"])
            elif data and "title" in data:
                snippets.append(f"[Policy: {data.get('title')}]")
        
        if snippets:
            return "\n".join(snippets)
        raise RuntimeError("Datastore indexing in progress. Please wait 10-30 minutes.")
        
    except Exception as e:
        return _read_local_policy(domain)

def _read_local_policy(domain: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if domain == "finops":
        path = os.path.join(base_dir, "policies", "finops", "Enterprise_FinOps_Routing_Policy_2026.txt")
    elif domain == "hr":
        path = os.path.join(base_dir, "policies", "hr", "HR_Privacy_Policy_2026.txt")
    else:
        raise ValueError(f"Unknown domain: {domain}")
        
    if not os.path.exists(path):
        alt_path = os.path.join(base_dir, "policies", "Enterprise_FinOps_Routing_Policy_2026.txt" if domain == "finops" else "HR_Privacy_Policy_2026.txt")
        if os.path.exists(alt_path):
            path = alt_path
            
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
