from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceInput(BaseModel):
    invoice_number: str
    vendor_name: str
    hsn_code: str
    taxable_value: float
    gst_rate: float  
    total_gst_charged: float

class TaxAuditResult(BaseModel):
    is_compliant: bool = Field(..., description="True if no tax errors are found")
    identified_errors: List[str] = Field(..., description="List of specific GST violations found")
    calculated_gst_amount: float = Field(..., description="The GST amount the AI calculated manually")
    suggested_hsn_code: Optional[str] = Field(None, description="The correct HSN code if the provided one is wrong")
    legal_reference: str = Field(..., description="The specific GST Section or Rule cited") # FIXED SPELLING
    confidence_score: float = Field(ge=0, le=1, description="AI's confidence in this audit")