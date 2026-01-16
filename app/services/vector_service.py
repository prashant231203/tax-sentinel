import chromadb 
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder
import numpy as np

default_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

client = chromadb.PersistentClient(path="./chromadb_store")

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
        n_results=n_results * 10 # Get 10x candidates to cast a wider net
    )
    
    documents = results['documents'][0]
    if not documents:
        return []

    # 1.5 Keyword Filter (If HSN provided)
    if filter_hsn:
        # Prioritize documents that contain the HSN code
        # We don't discard others yet, but we will boost scrore or filter here
        # Let's filter strictly as requested "prioritize chunks that explicitly contain"
        filtered_docs = [doc for doc in documents if filter_hsn in doc]
        if filtered_docs:
            documents = filtered_docs
            # If we successfully filtered, use these. If not, fallback to all (maybe it's a general rule)

    # 2. Re-rank candidates (Cross-Encoder)
    pairs = [[query_text, doc] for doc in documents]
    scores = reranker.predict(pairs)
    
    # 3. Sort by score
    sorted_indices = np.argsort(scores)[::-1]
    top_docs = [documents[i] for i in sorted_indices[:n_results]]
    
    return top_docs
