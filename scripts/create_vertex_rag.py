import os
import sys
from google.cloud import discoveryengine_v1
from google.api_core.client_options import ClientOptions

def create_vertex_resources(project_id: str, location: str, datastore_id: str, display_name: str, content: str):
    """Create a DataStore, Engine, and upload a document."""
    client_options = ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
    ds_client = discoveryengine_v1.DataStoreServiceClient(client_options=client_options)
    engine_client = discoveryengine_v1.EngineServiceClient(client_options=client_options)
    doc_client = discoveryengine_v1.DocumentServiceClient(client_options=client_options)

    parent = ds_client.collection_path(project_id, location, "default_collection")
    
    # 1. Create Data Store
    ds = discoveryengine_v1.DataStore(
        display_name=display_name,
        industry_vertical=discoveryengine_v1.IndustryVertical.GENERIC,
        solution_types=[discoveryengine_v1.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine_v1.DataStore.ContentConfig.CONTENT_REQUIRED,
    )
    ds_request = discoveryengine_v1.CreateDataStoreRequest(
        parent=parent,
        data_store_id=datastore_id,
        data_store=ds,
    )
    print(f"Creating DataStore {datastore_id}...")
    try:
        ds_operation = ds_client.create_data_store(request=ds_request)
        ds_operation.result(timeout=300)
        print(f"DataStore {datastore_id} created.")
    except Exception as e:
        print(f"Note: DataStore might already exist or error occurred: {e}")

    # 2. Create Engine
    engine_id = datastore_id
    engine = discoveryengine_v1.Engine(
        display_name=display_name,
        solution_type=discoveryengine_v1.SolutionType.SOLUTION_TYPE_SEARCH,
        data_store_ids=[datastore_id],
        search_engine_config=discoveryengine_v1.Engine.SearchEngineConfig(
            search_tier=discoveryengine_v1.SearchTier.SEARCH_TIER_STANDARD,
            search_add_ons=[]
        )
    )
    engine_request = discoveryengine_v1.CreateEngineRequest(
        parent=parent,
        engine_id=engine_id,
        engine=engine,
    )
    print(f"Creating Engine {engine_id}...")
    try:
        eng_operation = engine_client.create_engine(request=engine_request)
        eng_operation.result(timeout=300)
        print(f"Engine {engine_id} created.")
    except Exception as e:
        print(f"Note: Engine might already exist or error occurred: {e}")

    # 3. Import Document
    doc = discoveryengine_v1.Document(
        struct_data={"title": display_name},
        content=discoveryengine_v1.Document.Content(
            raw_bytes=content.encode("utf-8"),
            mime_type="text/plain"
        )
    )
    doc_request = discoveryengine_v1.CreateDocumentRequest(
        parent=doc_client.branch_path(project_id, location, datastore_id, "default_branch"),
        document=doc,
        document_id="policy_doc_1"
    )
    print(f"Uploading policy document for {datastore_id}...")
    try:
        doc_client.create_document(request=doc_request)
        print(f"Document uploaded to {datastore_id}.")
    except Exception as e:
        print(f"Note: Document might already exist or error occurred: {e}")

def main():
    project_id = os.environ.get("GCP_PROJECT_ID", "aerocaliper")
    location = "global"

    # FinOps
    create_vertex_resources(
        project_id=project_id,
        location=location,
        datastore_id="aerocaliper-rag_1714421160000",
        display_name="FinOps Policy",
        content="FinOps Policy: All workloads must use spot instances (use_spot: true) to optimize costs, regardless of urgency or executive approval. Do not use H200 or Blackwell instances for batch training."
    )

    # HR
    create_vertex_resources(
        project_id=project_id,
        location=location,
        datastore_id="aerocaliper-hr-rag",
        display_name="HR Privacy Policy",
        content="HR Policy: Employees must never send unredacted compensation, base salary, or PII in draft documents. Offer letters must go through the standard HR approval loop and be redacted."
    )

if __name__ == "__main__":
    main()
