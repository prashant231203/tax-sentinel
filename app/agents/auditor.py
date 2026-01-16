import os
import instructor
from dotenv import load_dotenv
from app.core.schemas import TaxAuditResult, InvoiceInput
from app.services.vector_service import query_knowledge_base # NEW: Connect Memory
from langsmith import traceable

load_dotenv()

client = instructor.from_provider(
    "groq/llama-3.3-70b-versatile", 
    api_key=os.getenv("GROQ_API_KEY"),
    async_client=True
)

# app/agents/auditor.py (Refined Version)

async def validate_context(hsn_code: str, context: str) -> bool:
    """Uses Gemini to check if the retrieved law is actually relevant."""
    # We use Gemini here for a 'Second Opinion'
    response = await client_gemini.create( # Assuming you set up Gemini client
        response_model=bool,
        messages=[
            {"role": "system", "content": f"Does this text contain the specific GST rate for HSN {hsn_code}? Return True or False."},
            {"role": "user", "content": context}
        ]
    )
    return response

@traceable(name="TaxSentinel_Agentic_RAG_Audit")
async def run_audit(invoice: InvoiceInput) -> TaxAuditResult:
    # 1. RETRIEVE
    search_query = f"GST rules and tax rates for HSN code {invoice.hsn_code}"
    relevant_chunks = query_knowledge_base(search_query)
    context_text = "\n---\n".join(relevant_chunks)
    
    # 2. VALIDATE
    is_relevant = await validate_context(invoice.hsn_code, context_text)
    
    if not is_relevant:
        # If the search failed, we don't let the AI guess.
        # We tell it specifically that the law is missing.
        context_text = "WARNING: No explicit law found in knowledge base for this HSN."

    # 3. AUDIT
    return await client.create(
        response_model=TaxAuditResult,
        messages=[
            {"role": "system", "content": "You are a Senior GST Auditor. Use the context. "
                                         "If the context is missing, say 'Law not found' in Legal Reference."},
            {"role": "user", "content": f"Audit this: {invoice.model_dump_json()}\nContext: {context_text}"}
        ]
    )