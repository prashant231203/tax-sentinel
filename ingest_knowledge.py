from app.utils.pdf_processor import extract_text_from_pdf, chunk_text
from app.services.vector_service import add_to_knowledge_base, reset_knowledge_base
import os
import re

def extract_hsn_from_chunk(text):
    # Regex to find 4, 6, or 8-digit HSN/SAC codes
    match = re.search(r'\b(99\d{2,6}|[0-8]\d{3,7})\b', text)
    return match.group(0) if match else None

def ingest_pdfs():
    knowledge_path = "./knowledgebase"
    
    # 1. Reset DB to remove old, bad chunks
    print("[!] Resetting Knowledge Base...")
    reset_knowledge_base()

    if not os.path.exists(knowledge_path):
        print(f"Error: Directory {knowledge_path} not found.")
        return

    files = [f for f in os.listdir(knowledge_path) if f.endswith(".pdf")]
    
    # Priority Filter: Only ingest Bare Laws for now (Rates are in JSON)
    bare_laws = [f for f in files if "Bare-Law" in f]
    if bare_laws:
        print(f"[*] Focusing on Bare Law documents: {bare_laws}")
        files = bare_laws
    
    if not files:
        print("No PDF files found to ingest.")
        return

    print(f"[*] Found {len(files)} documents to ingest.")
    
    for filename in files:
        print(f"[*] Processing {filename}...")
        
        # 2. Extract
        full_path = os.path.join(knowledge_path, filename)
        try:
            raw_text = extract_text_from_pdf(full_path)
        except Exception as e:
            print(f"[-] Failed to extract {filename}: {e}")
            continue
        
        if not raw_text:
            print(f"[-] Skipping {filename} (empty or failed extraction).")
            continue

        # 3. Chunk (Smart Chunking with Overlap)
        chunks = chunk_text(raw_text, chunk_size=500, overlap=100)
        
        if not chunks:
             print(f"[-] No text chunks generated for {filename}.")
             continue

        # 4. Prepare metadata
        # NEW: Tag chunks with HSN if found
        metadata = []
        for chunk in chunks:
            hsn = extract_hsn_from_chunk(chunk)
            meta = {"source": filename}
            if hsn:
                meta["hsn"] = hsn
            metadata.append(meta)

        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        
        # 5. Store in batches (OpenRouter/OpenAI Compatible)
        batch_size = 50 
        print(f"[*] Ingesting {len(chunks)} chunks in batches of {batch_size}...")

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_meta = metadata[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            
            try:
                add_to_knowledge_base(batch_chunks, batch_meta, batch_ids)
                print(f"   -> Batch {i//batch_size + 1}/{(len(chunks)//batch_size)+1} added.")
            except Exception as e:
                 print(f"❌ Batch Error: {e}")

if __name__ == "__main__":
    ingest_pdfs()