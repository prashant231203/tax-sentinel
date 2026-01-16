import os
from langsmith import traceable
from dotenv import load_dotenv

# Load environment variables (LANGCHAIN_API_KEY, etc.) 
# This ensures the tracer knows WHERE to send the data
load_dotenv()

# We define a standard decorator that you can import 
# into any other file (like auditor.py)
@traceable(
    run_type="chain", 
    name="TaxSentinel_Audit_Process"
)
def trace_ai_call(func):
    """
    A reusable decorator to wrap any AI function.
    It captures:
    - Function Inputs (The Invoice JSON)
    - Function Outputs (The Audit Report)
    - Latency and Error Traces
    """
    return func