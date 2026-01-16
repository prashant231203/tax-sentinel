from app.utils.pdf_processor import extract_text_from_pdf, chunk_text
from app.services.vector_service import add_to_knowledge_base
import os

def ingest_pdfs():
    knowledge_path = "./knowledgebase"
    
    for filename in os.listdir(knowledge_path):
        if filename.endswith(".pdf"):
            print(f"[*] Processing {filename}...")
            
            # 1. Extract
            raw_text = extract_text_from_pdf(os.path.join(knowledge_path, filename))
            
            # 2. Chunk
            chunks = chunk_text(raw_text)
            
            # 3. Prepare metadata (so the AI knows WHICH file the law came from)
            metadata = [{"source": filename} for _ in chunks]
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            
            # 4. Store
            add_to_knowledge_base(chunks, metadata, ids)

if __name__ == "__main__":
    ingest_pdfs()