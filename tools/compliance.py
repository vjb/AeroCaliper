import os
from google.cloud import discoveryengine_v1

def search_enterprise_policy(domain: str) -> str:
    """
    Query Vertex AI Search to fetch the relevant enterprise policy.
    Fails loud if GCP credentials are not found.
    """
    project_id = os.environ["GCP_PROJECT_ID"]
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
            # Standard edition doesn't return extractive segments, 
            # so we extract the raw struct_data that we uploaded
            data = result.document.struct_data
            if data and "content" in data:
                snippets.append(data["content"])
            elif data and "title" in data:
                snippets.append(f"[Policy: {data.get('title')}]")
        
        if snippets:
            return "\n".join(snippets)
        raise RuntimeError("Datastore indexing in progress. Please wait 10-30 minutes.")
        
    except Exception as e:
        raise RuntimeError(f"Vertex AI Search failed. Are GCP credentials configured? Error: {e}")
