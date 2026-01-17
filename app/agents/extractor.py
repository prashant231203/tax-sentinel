import os
import base64
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from app.core.schemas import InvoiceInput
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

load_dotenv()

# CRITICAL: Fail fast if API key is missing
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("CRITICAL: GROQ_API_KEY is not set.")

# Initialize Groq Client
client = instructor.from_openai(
    OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    ),
    mode=instructor.Mode.JSON
)

@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=15, max=120),
    retry=retry_if_exception_type(openai.RateLimitError)
)
def extract_from_invoice(file_path: str) -> InvoiceInput:
    """Extracts structured data from Image or PDF using Groq (Llama Vision)."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect file type
    mime_type = "application/pdf" if file_path.lower().endswith(".pdf") else "image/jpeg"
    
    print(f"[*] Vision Agent (Groq) is reading {mime_type}: {file_path}")

    # Encode file to Base64
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    data_url = f"data:{mime_type};base64,{encoded_string}"

    # Call Groq (Llama 4 Scout Vision)
    return client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        response_model=InvoiceInput,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": (
                            "Extract the full invoice data into the structured schema. "
                            "CRITICAL: Extract the 'items' list accurately. Capture every row in the table. "
                            "Ensure 'gst_rate_charged' is the percentage (e.g. 18, not 0.18)."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    }
                ]
            }
        ],
    )
