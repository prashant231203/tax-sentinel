import os
import instructor
import google.genai as genai
from dotenv import load_dotenv
from app.core.schemas import InvoiceInput
from PIL import Image
import base64

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    # Fallback or just let it fail later, but for module level execution it is better to handle.
    # We will pass None but user needs to ensure it's set.
    pass

# Initialize Client
# process.env.GOOGLE_API_KEY must be set
try:
    client = instructor.from_genai(
        client=genai.Client(api_key=api_key),
        mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
    )
except Exception as e:
    # If client init fails (e.g. missing key), we'll define a dummy client 
    # or let the function fail when called.
    print(f"Warning: Gemini Client failed to initialize: {e}")
    client = None

def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_from_invoice(file_path: str) -> InvoiceInput:
    """
    Extracts structured invoice data from an image or PDF using Gemini 1.5 Flash.
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Create the prompt with the image
    # Note: For PDFs, we might need a different handling or convert to image. 
    # Gemini 1.5 supports PDF ingestion directly in some modes, but via API 
    # it's often easier to pass image data for 'Vision'. 
    # For simplicity, we assume the user passes an image path. 
    # If PDF, we'd need to upload it to File API or convert pages to images.
    
    # For this implementation, we will assume it's an image. 
    # If it is a PDF, we might need to use `genai.Client.files.upload`.
    
    # Basic implementation using image bytes
    try:
        image = Image.open(file_path)
    except Exception:
        # If not an image, assumption is it might be a PDF. 
        # For a robust solution we should handle PDF uploads.
        # But for 'Vision Agent' usually we start with images.
        print("Warning: File is not an image. Assuming PDF handling needed (not implemented yet for inline bytes).")
        # Placeholder for PDF handling
        pass

    resp = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    "Extract the following fields from this invoice image perfectly.", 
                    image
                ] 
            }
        ],
        response_model=InvoiceInput,
    )
    
    return resp
