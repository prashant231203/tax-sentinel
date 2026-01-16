from pypdf import PdfReader

def extreact_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from the pdf."""
    reader = PdfReader(pdf_path)
    text=""
    for page in reader.pages:
        text += page.extract_text()
    return text
def chunk_text(text: str, chunk_size: int = 1000)-> list[str]:
    """Breaks the long text into smaller pieces chunks fr the aI"""

    #this is the simple version of 'recursiveCharacterTextSplitter'
    return [text[i:i+chunk_size] for i in range(0, len(text),chunk_size)]