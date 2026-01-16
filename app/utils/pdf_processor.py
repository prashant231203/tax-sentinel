from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from the pdf."""
    try:
        reader = PdfReader(pdf_path)
        text=""
        for i, page in enumerate(reader.pages):
            try:
                content = page.extract_text()
                if content:
                    text += content
            except Exception as e:
                print(f"Warning: Failed to extract text from page {i+1} in {pdf_path}: {e}")
                continue
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""
def chunk_text(text: str, chunk_size: int = 1000)-> list[str]:
    """Breaks the long text into smaller pieces chunks fr the aI"""

    #this is the simple version of 'recursiveCharacterTextSplitter'
    return [text[i:i+chunk_size] for i in range(0, len(text),chunk_size)]