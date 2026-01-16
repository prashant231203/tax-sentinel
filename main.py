import asyncio
from dotenv import load_dotenv
import os

# Load environment variables before importing modules that might use them
load_dotenv()

from app.agents.auditor import run_audit
from app.agents.extractor import extract_from_invoice
from app.core.schemas import InvoiceInput
import sys
import time

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
        invoice_data = InvoiceInput(
            invoice_number="SENTINEL-MOCK-001",
            vendor_name="Varanasi Tech Solutions",
            hsn_code="998311",
            taxable_value=1000.0,
            gst_rate=0.18,
            total_gst_charged=250.0 # Intentional Error (Should be 180)
        )

    # 2. AUDIT PROCESS (With RAG + Validator)
    print(f"[*] Starting Audit for HSN {invoice_data.hsn_code}...")
    try:
        result = await run_audit(invoice_data)
        
        # 3. REPORTING
        print("\n=== TAX SENTINEL AUDIT REPORT ===")
        print(f"Status:      {'✅ COMPLIANT' if result.is_compliant else '❌ NON-COMPLIANT'}")
        print(f"Confidence:  {result.confidence_score * 100:.1f}%")
        
        if not result.is_compliant:
            print("\n[!] VIOLATIONS FOUND:")
            for error in result.identified_errors:
                print(f" - {error}")
            
            print(f"\n[i] TECHNICAL DETAILS:")
            print(f"   Calculated GST: {result.calculated_gst_amount}")
            print(f"   Charged GST:    {invoice_data.total_gst_charged}")
            print(f"   Discrepancy:    {invoice_data.total_gst_charged - result.calculated_gst_amount}")
            
        print(f"\n[§] LEGAL REFERENCE:\n{result.legal_reference}")
    except Exception as e:
        print(f"[-] Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())