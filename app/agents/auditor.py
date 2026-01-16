import os
import json
import asyncio
import instructor
from openai import AsyncOpenAI 
from dotenv import load_dotenv
from app.core.schemas import TaxAuditResult, InvoiceInput
from app.services.vector_service import query_knowledge_base
from app.agents.validator import validate_retrieval
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

load_dotenv()

# Initialize the OpenRouter Client
base_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://taxsentinel.com"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "TaxSentinel"),
    }
)

client = instructor.from_openai(base_client, mode=instructor.Mode.JSON)

# Load HSN Rates (Fact Base) - Deterministic Memory
HSN_RATES = {}
try:
    with open("app/core/hsn_rates.json", "r") as f:
        HSN_RATES = json.load(f)
    print(f"✅ Loaded {len(HSN_RATES)} HSN rates from Fact Base.")
except Exception as e:
    print(f"⚠️ Warning: Could not load HSN Rates JSON: {e}")

@traceable(name="TaxSentinel_OpenRouter_Audit")
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=15, max=120),
    retry=retry_if_exception_type(openai.RateLimitError)
)
async def run_audit(invoice: InvoiceInput) -> TaxAuditResult:
    print(f"[*] Auditing Invoice with HSN: {invoice.hsn_code}")
    
    # 1. HARD LOOKUP (Deterministic)
    fact_context = ""
    hsn_clean = str(invoice.hsn_code).replace(" ", "").replace(".", "").strip()
    
    # Strategy: Exact match -> 6 digit -> 4 digit -> 2 digit
    rate_info = HSN_RATES.get(hsn_clean)
    if not rate_info and len(hsn_clean) > 4:
         rate_info = HSN_RATES.get(hsn_clean[:6])
    if not rate_info and len(hsn_clean) > 4:
         rate_info = HSN_RATES.get(hsn_clean[:4])
         
    if rate_info:
        # DYNAMIC CITATION: Use the legal_ref if available, else generic.
        legal_ref = rate_info.get('legal_ref', 'Notification No. 11/2017-Central Tax (Rate)')
        fact_context = f"✅ KNOWN FACT: For HSN {hsn_clean}, the prescribed GST Rate is {rate_info['rate']}.\n   Description: {rate_info['description']}.\n   Source Authority: {legal_ref}"
        print(f"[*] Fact Hit: {fact_context}")
    else:
        fact_context = f"⚠️ FACT MISSING: HSN {hsn_clean} not found in Master Rate List."
        print("[!] Fact Miss: Relying solely on RAG.")

    # 2. RETRIEVE (Probabilistic - for Rules/Sections)
    search_query = f"GST rules, valuation section, and penalty for HSN {invoice.hsn_code}"
    # Use the filter we added to vector_service to prioritize matching HSN chunks
    relevant_chunks = query_knowledge_base(search_query, filter_hsn=invoice.hsn_code)
    
    context_text = "\n---\n".join(relevant_chunks)
    
    # 3. VALIDATE
    # Only validate if we didn't find a hard fact, OR if we want to ensure sections are correct.
    validation = await validate_retrieval(search_query, context_text)
    if not validation.is_relevant:
        print(f"⚠️ Retrieval Warning: {validation.reason}")
    
    # RATE LIMIT BUFFER for FREE TIER
    print("[*] Cooling down for 10 seconds before Final Audit...")
    await asyncio.sleep(10)

    # 4. AUDIT
    return await client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free", 
        response_model=TaxAuditResult,
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a Senior GST Auditor. "
                    "STRICT RULES: "
                    "1. TRUST THE DATA: If the Fact Base mentions a rate reduction (e.g., 'Reduced from X to Y'), ALWAYS use the new 'To' rate (Y). "
                    "2. SUB-CATEGORY CHECK: If a rate has 'SPLIT CATEGORY' (e.g., Tractors), you MUST check the Invoice Description. "
                    "   - If Description matches 'Agricultural', use the lower rate. "
                    "   - If 'Road' or >1800cc, use the higher rate. "
                    "3. CORRECT CITATION: "
                    "   - For GOODS (machines, products): Cite 'Notification No. 1/2017-Central Tax (Rate)'. "
                    "   - For SERVICES (consulting, labor): Cite 'Notification No. 11/2017-Central Tax (Rate)'. "
                    "   - If 'type' is provided in Fact Base, follow it. "
                    "4. CONFIDENCE: If the Invoice Description is vague for a Split Category, lower your confidence to 70%."
                )
            },
            {
                "role": "user", 
                "content": (
                    f"INVOICE DATA: {invoice.model_dump_json()}\n\n"
                    f"--- FACT BASE ---\n{fact_context}\n\n"
                    f"--- LEGAL CONTEXT ---\n{context_text}\n"
                )
            }
        ]
    )
