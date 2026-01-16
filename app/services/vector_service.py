import chromadb
import os 
from chromadb.utils import embedding_functions
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Switch to OpenRouter Embeddings (More reliable than Google Free Tier)
# We use the OpenAI-compatible endpoint of OpenRouter
api_key = os.getenv("OPENROUTER_API_KEY")

default_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=api_key,
    api_base="https://openrouter.ai/api/v1",
    model_name="openai/text-embedding-3-small" 
)

client = chromadb.PersistentClient(path="./chromadb_store")

try:
    collection = client.get_or_create_collection(
        name = "gst_laws",
        embedding_function=default_ef
    )
except ValueError as e:
    print(f"⚠️ Embedding Function Conflict ({e}). Resetting collection...")
    client.delete_collection("gst_laws")
    collection = client.get_or_create_collection(
        name = "gst_laws",
        embedding_function=default_ef
    )

def reset_knowledge_base():
    """Clears the existing knowledge base."""
    global collection
    client.delete_collection("gst_laws")
    collection = client.get_or_create_collection(
        name = "gst_laws",
        embedding_function=default_ef
    )
    print("♻️  Knowledge Base successfully reset.")

def add_to_knowledge_base(chunks: list[str], metadata: list[dict], ids: list[str]):
    """Stores text chunks in the Database."""
    collection.add(
        documents=chunks,
        metadatas=metadata,
        ids=ids
    )
    print(f"✅ Successfully added {len(chunks)} chunks to the knowledge base.")

def query_knowledge_base(query_text: str, n_results: int = 3, filter_hsn: str = None):
    """Searches for the most relevant tax laws with Re-ranking."""
    # 1. Retrieve more candidates (Vector Search)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results * 5 # Get 5x candidates to cast a wider net
    )
    
    documents = results['documents'][0]
    if not documents:
        return []

    # 1.5 Keyword Filter (If HSN provided)
    if filter_hsn:
        # Prioritize documents that contain the HSN code
        # We search both metadata 'hsn' tag AND text body
        filtered_docs = [
            doc for i, doc in enumerate(documents) 
            if filter_hsn in doc or (results['metadatas'] and results['metadatas'][0][i].get('hsn') == filter_hsn)
        ]
        if filtered_docs:
            documents = filtered_docs
            # If we successfully filtered, use these. If not, fallback to all (maybe it's a general rule)

    # 2. Return Top Results with Metadata
    # We construct a string that includes the Source filename explicitly
    formatted_results = []
    
    # query returns: {'ids': [...], 'distances': [...], 'metadatas': [[{m1}, {m2}]], 'documents': [[...]]}
    retrieved_docs = documents[:n_results]
    # metadatas is a list of lists (one list per query). We only have 1 query.
    retrieved_metas = results['metadatas'][0][:n_results] if results['metadatas'] else [{}] * len(retrieved_docs)

    for doc, meta in zip(retrieved_docs, retrieved_metas):
        source = meta.get('source', 'Unknown Document')
        formatted_results.append(f"SOURCE DOCUMENT: {source}\nCONTENT: {doc}")

    return formatted_results
