import chromadb 
from chromadb.utils import embedding_functions

default_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chromadb_store")

collection = client.get_or_create_collection(
    name = "gst_laws",
    embedding_function=default_ef
)

def add_to_knowledge_base(chunks: list[str], metadata: list[dict], ids: list[str]):
    """Stores text chunks in the Database."""
    collection.add(
        documents=chunks,
        metadatas=metadata,
        ids=ids
    )
    print(f"✅ Successfully added {len(chunks)} chunks to the knowledge base.")

def query_knowledge_base(query_text: str, n_results: int = 3):
    """Searches for the most relevant tax laws."""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results['documents'][0] # Returns the top relevant text chunks
