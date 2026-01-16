import os
import instructor
from dotenv import load_dotenv
from app.core.schemas import TaxAuditResult, InvoiceInput
from langsmith import traceable

# STEP 1: Load the environment variables IMMEDIATELY
load_dotenv()

# STEP 2: Verify the key exists. If this fails, the error will be clear.
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("CRITICAL ERROR: GROQ_API_KEY not found in .env file or environment variables.")

# STEP 3: Initialize the client using the key explicitly
# This removes all "guessing" by the library
client = instructor.from_provider(
    "groq/llama-3.3-70b-versatile", 
    api_key=api_key, # Explicitly pass the key here
    async_client=True
)

@traceable(name="TaxSentinel_GST_Auditor")
async def run_audit(invoice: InvoiceInput) -> TaxAuditResult:
    """The core auditing logic using the Unified Instructor Client."""
    return await client.create(
        response_model=TaxAuditResult,
        messages=[
            {
                "role": "system", 
                "content": "You are a professional Indian GST Auditor. "
                           "Identify tax math errors and cite CGST/SGST Rules."
            },
            {
                "role": "user", 
                "content": f"Audit this invoice: {invoice.model_dump_json()}"
            }
        ]
    )