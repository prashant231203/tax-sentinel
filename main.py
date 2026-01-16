import asyncio
from dotenv import load_dotenv
import os

# Load environment variables before importing modules that might use them
load_dotenv()

from app.agents.auditor import run_audit
from app.core.schemas import InvoiceInput

async def test_system():
    # INTENTIONAL ERROR: 18% of 1000 is 180, but we charge 250.
    test_invoice = InvoiceInput(
        invoice_number="SENTINEL-001",
        vendor_name="Varanasi Tech Solutions",
        hsn_code="998311",
        taxable_value=1000.0,
        gst_rate=0.18,
        total_gst_charged=250.0
    )

    print("[*] Dispatching TaxSentinel Auditor...")
    try:
        report = await run_audit(test_invoice)
        
        print("\n--- SENTINEL AUDIT REPORT ---")
        print(f"Compliant: {'✅ YES' if report.is_compliant else '❌ NO'}")
        print(f"Violations: {report.identified_errors}")
        print(f"Calculated GST: ₹{report.calculated_gst_amount}")
        print(f"Legal Reference: {report.legal_reference}")
        print(f"Confidence: {int(report.confidence_score * 100)}%")
        
    except Exception as e:
        print(f"ERROR: Something went wrong during the audit: {e}")

if __name__ == "__main__":
    asyncio.run(test_system())