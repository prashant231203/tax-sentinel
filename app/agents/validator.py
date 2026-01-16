import instructor
from openai import AsyncOpenAI
import os
from pydantic import BaseModel, Field
from langsmith import traceable
from tenacity import retry,  stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

class RelevanceResult(BaseModel):
    is_relevant: bool = Field(..., description="True if the context contains information relevant to the user query.")
    reason: str = Field(..., description="Why valid or invalid.")

# Initialize OpenRouter Client
api_key = os.getenv("OPENROUTER_API_KEY")
base_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://taxsentinel.com"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "TaxSentinel"),
    }
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
        model="google/gemini-2.0-flash-exp:free", 
        response_model=RelevanceResult,
        messages=[
            {"role": "system", "content": "You are a legal search validator. Check if the provided Context contains laws relevant to the Query."},
            {"role": "user", "content": f"Query: {query}\n\nContext: {context}"}
        ]
    )
