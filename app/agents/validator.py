import instructor
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langsmith import traceable
from tenacity import retry,  stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

load_dotenv()

class RelevanceResult(BaseModel):
    is_relevant: bool = Field(..., description="True if the context contains information relevant to the user query.")
    reason: str = Field(..., description="Why valid or invalid.")

# Initialize Groq Client
api_key = os.getenv("GROQ_API_KEY")
base_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key,
)
client = instructor.from_openai(base_client, mode=instructor.Mode.JSON)

@traceable(name="TaxSentinel_Validator")
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=2, min=15, max=120),
    retry=retry_if_exception_type(openai.RateLimitError)
)
async def validate_retrieval(query: str, context: str) -> RelevanceResult:
    """
    Checks if the retrieved legal context is actually relevant to the audit query.
    """
    return await client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        response_model=RelevanceResult,
        messages=[
            {"role": "system", "content": "You are a legal search validator. Check if the provided Context contains laws relevant to the Query."},
            {"role": "user", "content": f"Query: {query}\n\nContext: {context}"}
        ]
    )
