from app.utils.pdf_processor import extract_text_from_pdf, chunk_text
from app.services.vector_service import add_to_knowledge_base, reset_knowledge_base
import os

def ingest_pdfs():
    knowledge_path = "./knowledgebase"
    
    # 1. Reset DB to remove old, bad chunks
    print("[!] Resetting Knowledge Base...")
    reset_knowledge_base()

    if not os.path.exists(knowledge_path):
        print(f"Error: Directory {knowledge_path} not found.")
        return

    files = [f for f in os.listdir(knowledge_path) if f.endswith(".pdf")]
    if not files:
        print("No PDF files found to ingest.")
        return

    print(f"[*] Found {len(files)} documents to ingest.")
    
    for filename in files:
        print(f"[*] Processing {filename}...")
        
        # 2. Extract
        full_path = os.path.join(knowledge_path, filename)
        raw_text = extract_text_from_pdf(full_path)
        
        if not raw_text:
            print(f"[-] Skipping {filename} (empty or failed extraction).")
            continue

        # 3. Chunk (Smart Chunking with Overlap)
        chunks = chunk_text(raw_text, chunk_size=1000, overlap=200)
        
        if not chunks:
             print(f"[-] No text chunks generated for {filename}.")
             continue

        # 4. Prepare metadata
        metadata = [{"source": filename} for _ in chunks]
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        
        # 5. Store
        add_to_knowledge_base(chunks, metadata, ids)

if __name__ == "__main__":
    ingest_pdfs()