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

# Initialize Groq Client
base_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
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

from app.utils.reconciler import validate_invoice_math

@traceable(name="TaxSentinel_OpenRouter_Audit")
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=15, max=120),
    retry=retry_if_exception_type(openai.RateLimitError)
)
async def run_audit(invoice: InvoiceInput) -> TaxAuditResult:
    print(f"[*] Auditing Invoice Items ({len(invoice.items)} items)...")
    
    technical_violations = []
    legal_violations = []
    consolidated_calculated_gst = 0.0
    primary_legal_ref = "Multiple - See Item Details"
    
    # 0. Deterministic Math Check (Reconciler)
    is_math_valid, math_errors = validate_invoice_math(invoice)
    if not is_math_valid:
        technical_violations.extend(math_errors)
        print(f"[!] Math Errors Detected: {len(math_errors)}")

    # Loop through items
    fact_context_accumulator = []
    
    for i, item in enumerate(invoice.items):
        print(f"[*] processing Item {i+1}: {item.hsn_code} - {item.description}")
        
        # 1. HARD LOOKUP (Deterministic)
        hsn_clean = str(item.hsn_code).replace(" ", "").replace(".", "").strip()
        
        # Strategy: Exact match -> 6 digit -> 4 digit -> 2 digit
        rate_info = HSN_RATES.get(hsn_clean)
        # Fallback logic
        if not rate_info and len(hsn_clean) > 4: rate_info = HSN_RATES.get(hsn_clean[:6])
        if not rate_info and len(hsn_clean) > 4: rate_info = HSN_RATES.get(hsn_clean[:4])
            
        if rate_info:
            legal_ref = rate_info.get('legal_ref', 'Notification No. 11/2017-Central Tax (Rate)')
            # Only set primary ref if it's the first one found
            if primary_legal_ref == "Multiple - See Item Details": primary_legal_ref = legal_ref
            
            fact_context_accumulator.append(
                f"✅ KNOWN FACT (Item {i+1}): HSN {hsn_clean} -> Rate {rate_info['rate']}. Source: {legal_ref}"
            )
            
            # DETERMINISTIC RATE CHECK (Bypass LLM if we have hard fact)
            # Parse rate string "18%" -> 18.0
            try:
                base_rate = float(rate_info['rate'].replace('%', '').strip())
                if abs(base_rate - item.gst_rate_charged) > 0.5:
                     legal_violations.append(
                         f"Item {i+1} ({item.description}): Rate Mismatch. "
                         f"Charged {item.gst_rate_charged}%, Valid is {base_rate}%."
                     )
            except:
                pass # If complex rate like "5% or 18%", let LLM handle it
                
        else:
            fact_context_accumulator.append(f"⚠️ FACT MISSING (Item {i+1}): HSN {hsn_clean} not found.")

    fact_context = "\n".join(fact_context_accumulator)


        # Accumulated Calculation
        # We use the CHARGED rate for math verification (done in Step 0), 
        # but here we could track 'correct' tax if we wanted. 
        # For this 'commercial grade' version, we trust the Reconciler for math 
        # and the Fact lookup for Legal.
        
    # 2. RETRIEVE (Probabilistic - ONE PASS for entire invoice context or major items)
    # Optimization: Just query for the first/major HSN to get general legal context
    search_query = f"GST rules for HSN {invoice.items[0].hsn_code}"
    relevant_chunks = query_knowledge_base(search_query, filter_hsn=invoice.items[0].hsn_code)
    context_text = "\n---\n".join(relevant_chunks)
    
    # 3. VALIDATE
    validation = await validate_retrieval(search_query, context_text)
    
    # RATE LIMIT BUFFER for FREE TIER
    print("[*] Cooling down for 10 seconds before Final Audit...")
    await asyncio.sleep(10)

    # 4. AUDIT (The "Prosecutor" LLM Pass)
    # We feed it the violations we already found deterministically
    deterministic_notes = ""
    if technical_violations: 
        deterministic_notes += f"\n[AUTO-DETECTED MATH ERRORS]:\n- " + "\n- ".join(technical_violations)
    if legal_violations:
        deterministic_notes += f"\n[AUTO-DETECTED RATE ERRORS]:\n- " + "\n- ".join(legal_violations)

    return await client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        response_model=TaxAuditResult,
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a Senior GST Auditor. "
                    "Analyze the invoice data and the auto-detected errors."
                    "STRICT RULES: "
                    "1. If [AUTO-DETECTED] errors exist, you MUST include them in your final report. "
                    "2. Verify the auto-findings against the Fact Base. "
                    "3. For compliance, 'math_compliant' is False only if math errors exist. 'is_compliant' is False if ANY error exists."
                )
            },
            {
                "role": "user", 
                "content": (
                    f"INVOICE ITEMS: {invoice.model_dump_json()}\n\n"
                    f"--- FACT BASE (Sample) ---\n{fact_context}\n\n"
                    f"--- DETERMINISTIC FINDINGS ---\n{deterministic_notes}\n\n"
                    f"--- LEGAL CONTEXT ---\n{context_text}\n"
                )
            }
        ]
    )
