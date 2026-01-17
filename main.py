import asyncio
from dotenv import load_dotenv
import os
import logging

# Load environment variables before importing modules that might use them
load_dotenv()

# High-Priority: Sanitize Loggers (Silence Library Noise)
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from app.agents.auditor import run_audit
from app.agents.extractor import extract_from_invoice
from app.core.schemas import InvoiceInput
import sys
import time

def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"

async def main():
    invoice_data = None
    
    # 1. VISUAL EXTRACTION (If file provided)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"[*] Extracting data from {file_path} using Vision Agent...")
        try:
            invoice_data = extract_from_invoice(file_path)
            print(f"[+] Extracted Invoice: {invoice_data.invoice_number} from {invoice_data.vendor_name}")
            
            # RATE LIMIT BUFFER: Gemini 2.0 Flash Free Tier has very low RPM (sometimes 0/15).
            # We must wait to avoid '429 RESOURCE_EXHAUSTED' burst errors.
            print("[*] Cooling down for 30 seconds to respect Rate Limits...")
            await asyncio.sleep(30) 

        except Exception as e:
            print(f"[-] Extraction failed: {e}")
            return
    else:
        # Fallback to Mock Data
        print("[*] No file provided. Using Mock Invoice for simulation.")
        from app.core.schemas import InvoiceItem
        invoice_data = InvoiceInput(
            invoice_number="SENTINEL-MOCK-001",
            vendor_name="Varanasi Tech Solutions",
            items=[
                InvoiceItem(
                    description="IT Consulting",
                    hsn_code="998311",
                    taxable_value=1000.0,
                    gst_rate_charged=18.0,
                    gst_amount_charged=180.0
                )
            ],
            total_taxable_value=1000.0,
            total_gst_amount=250.0 # Intentional Math Error (Total says 250, Item says 180)
        )

    # 2. AUDIT PROCESS (With RAG + Validator)
    print(f"[*] Starting Audit for Invoice {invoice_data.invoice_number}...")
    try:
        result = await run_audit(invoice_data)
        
        # 3. REPORTING
        print("\n=== TAX SENTINEL AUDIT REPORT ===")
        print(f"Status:      {'✅ COMPLIANT' if result.is_compliant else '❌ NON-COMPLIANT'}")
        print(f"Math Check:  {'✅ PASS' if result.math_compliant else '❌ FAIL'}")
        print(f"Confidence:  {result.confidence_score * 100:.1f}%")
        
        if not result.is_compliant:
            print("\n[!] VIOLATIONS FOUND:")
            for error in result.identified_errors:
                print(f" - {error}")
            
            print(f"\n[i] TECHNICAL DETAILS:")
            print(f"   Calculated GST: {format_currency(result.calculated_gst_amount)}")
            print(f"   Charged GST:    {format_currency(invoice_data.total_gst_amount)}")
            print(f"   Discrepancy:    {format_currency(invoice_data.total_gst_amount - result.calculated_gst_amount)}")
            
        print(f"\n[§] LEGAL REFERENCE:\n{result.legal_reference}")
    except Exception as e:
        print(f"[-] Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())