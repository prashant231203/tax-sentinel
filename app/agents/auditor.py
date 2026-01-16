import os
import instructor
from openai import AsyncOpenAI # Use the OpenAI client for OpenRouter
from dotenv import load_dotenv
from app.core.schemas import TaxAuditResult, InvoiceInput
from app.services.vector_service import query_knowledge_base
from app.agents.validator import validate_retrieval
from langsmith import traceable

load_dotenv()

# Initialize the OpenRouter Client
# This single client can now call Llama, Claude, or Gemini
base_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME"),
    }
)

# Patch the client with Instructor
client = instructor.from_openai(base_client, mode=instructor.Mode.JSON)

@traceable(name="TaxSentinel_OpenRouter_Audit")
async def run_audit(invoice: InvoiceInput) -> TaxAuditResult:
    # 1. RETRIEVE
    search_query = f"GST rules and tax rates for HSN code {invoice.hsn_code}"
    # Pass HSN code for explicit filtering
    relevant_chunks = query_knowledge_base(search_query, filter_hsn=invoice.hsn_code)
    context_text = "\n---\n".join(relevant_chunks)
    
    # 2. VALIDATE
    validation = await validate_retrieval(search_query, context_text)
    if not validation.is_relevant:
        print(f"⚠️ Retrieval Warning: {validation.reason}")
        # Optionally, we could fallback to general knowledge or trigger a broader search here
    
    # 3. AUDIT (Using a high-limit model on OpenRouter)
    # You can use 'anthropic/claude-3.5-sonnet' or 'meta-llama/llama-3.1-405b'
    return await client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct", 
        response_model=TaxAuditResult,
        messages=[
            {"role": "system", "content": "You are a professional GST Auditor. If the provided legal context does not explicitly mention the specific HSN code from the invoice, report 'NO RELEVANT LAW FOUND' in the legal reference field instead of guessing a Section number or hallucinating a match."},
            {"role": "user", "content": f"Audit this: {invoice.model_dump_json()}\nContext: {context_text}"}
        ]
    )