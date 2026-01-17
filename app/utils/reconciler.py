from typing import List, Tuple
from app.core.schemas import InvoiceInput

def validate_invoice_math(invoice: InvoiceInput) -> Tuple[bool, List[str]]:
    """
    Deterministically checks if the invoice sums match the item details.
    Returns (is_math_valid, list_of_math_errors).
    """
    errors = []
    
    # 1. Check Total Taxable Value
    calculated_total_taxable = sum(item.taxable_value for item in invoice.items)
    if abs(calculated_total_taxable - invoice.total_taxable_value) > 1.0:
        errors.append(
            f"Math Error: Sum of item taxable values ({calculated_total_taxable}) "
            f"does not match invoice total taxable value ({invoice.total_taxable_value})."
        )

    # 2. Check Total GST Amount
    calculated_total_gst = sum(item.gst_amount_charged for item in invoice.items)
    if abs(calculated_total_gst - invoice.total_gst_amount) > 1.0:
        errors.append(
            f"Math Error: Sum of item tax amounts ({calculated_total_gst}) "
            f"does not match invoice total tax amount ({invoice.total_gst_amount})."
        )
        
    # 3. Check Individual Item Logic (Rate * Value = Amount)
    for i, item in enumerate(invoice.items):
        expected_tax = item.taxable_value * (item.gst_rate_charged / 100.0)
        if abs(expected_tax - item.gst_amount_charged) > 1.0:
            errors.append(
                f"Line Item {i+1} ({item.description}): Math mismatch. "
                f"{item.taxable_value} * {item.gst_rate_charged}% should be {expected_tax:.2f}, "
                f"but is {item.gst_amount_charged}."
            )

    return (len(errors) == 0), errors
