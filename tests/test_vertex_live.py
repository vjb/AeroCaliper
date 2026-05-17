import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_vertex_search():
    print("Testing Vertex AI Search Data Store...")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_SEARCH_LOCATION", "global")
    datastore_id = os.getenv("VERTEX_DATASTORE_ID")

    if not project_id:
        print("FAIL: GOOGLE_CLOUD_PROJECT is not set.")
        sys.exit(1)
    if not datastore_id:
        print("FAIL: VERTEX_DATASTORE_ID is not set.")
        sys.exit(1)

    try:
        from google.cloud import discoveryengine_v1 as discoveryengine
    except ImportError:
        print("FAIL: google-cloud-discoveryengine not installed.")
        sys.exit(1)

    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_config"
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query="FinOps Routing Policy Spot Instances Budget Tag",
            page_size=1,
        )
        
        response = client.search(request)
        snippets = []
        for result in response.results:
            for ext in result.document.derived_struct_data.get("extractive_answers", []):
                snippets.append(ext.get("content", ""))
        
        if snippets:
            print(f"PASS: Found snippets: {snippets}")
            sys.exit(0)
        else:
            print("FAIL: No snippets found in datastore.")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_vertex_search()
