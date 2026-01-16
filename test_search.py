from app.services.vector_service import query_knowledge_base

# Test a real GST query based on the files you ingested
query = "What are the rules for HSN code 9983?"
results = query_knowledge_base(query)

print("\n--- KNOWLEDGE RETRIEVAL TEST ---")
for i, doc in enumerate(results):
    print(f"\nResult {i+1}:")
    print(doc[:300] + "...") # Print first 300 chars of the chunk