from pypdf import PdfReader

import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from the pdf with basic cleaning."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            try:
                content = page.extract_text()
                if content:
                    # Basic cleaning: Replace multiple spaces/newlines to keep it somewhat structured but dense
                    cleaned_content = re.sub(r'\s+', ' ', content).strip()
                    text_parts.append(cleaned_content)
            except Exception as e:
                print(f"Warning: Failed to extract text from page {i+1} in {pdf_path}: {e}")
                continue
        return " ".join(text_parts) # Join with space to prevent glued words across pages
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Splits text into chunks with overlap, respecting sentence boundaries where possible.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        
        # If we are not at the end of text, try to find a sentence break to cut
        if end < text_len:
            # Look for the last period/newline within the chunk limit
            # We search backwards from 'end' to 'start + chunk_size/2' (don't go too far back)
            lookback_limit = max(start, end - 200) 
            
            # Simple heuristic: Split on ". " or matching punctuation
            last_period = text.rfind('. ', lookback_limit, end)
            if last_period != -1:
                end = last_period + 1 # Include the period
            else:
                 # Try finding a space if no period
                last_space = text.rfind(' ', lookback_limit, end)
                if last_space != -1:
                    end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, but minus overlap to keep context
        start = end - overlap
        
        # Ensure we always move forward
        if start >= end:
            start = end

    return chunks