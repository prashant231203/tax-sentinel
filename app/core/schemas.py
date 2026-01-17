from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceItem(BaseModel):
    description: str = Field(..., description="Description of the goods or services")
    hsn_code: str = Field(..., description="The HSN/SAC code for this line item")
    taxable_value: float = Field(..., description="The value on which tax is calculated")
    gst_rate_charged: float = Field(..., description="The rate percentage charged (e.g., 18.0 for 18%)")
    gst_amount_charged: float = Field(..., description="The actual tax amount charged for this item")

class InvoiceInput(BaseModel):
    invoice_number: str
    vendor_name: str
    supplier_gstin: Optional[str] = None
    recipient_gstin: Optional[str] = None
    items: List[InvoiceItem] = Field(..., description="List of all line items in the invoice")
    total_taxable_value: float
    total_gst_amount: float

class TaxAuditResult(BaseModel):
    is_compliant: bool = Field(..., description="True if no tax errors are found")
    math_compliant: bool = Field(..., description="True if the invoice internal math is correct")
    identified_errors: List[str] = Field(..., description="List of specific GST violations found")
    calculated_gst_amount: float = Field(..., description="The total GST amount the AI calculated manually")
    legal_reference: str = Field(..., description="The specific GST Section or Rule cited")
    confidence_score: float = Field(ge=0, le=1, description="AI's confidence in this audit")