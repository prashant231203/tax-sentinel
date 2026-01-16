import instructor
from openai import AsyncOpenAI
import os
from pydantic import BaseModel, Field
from langsmith import traceable

class RelevanceResult(BaseModel):
    is_relevant: bool = Field(..., description="True if the context contains information relevant to the user query.")
    reason: str = Field(..., description="Why valid or invalid.")

# Initialize independent client for Validator (can be lighter model)
base_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
     default_headers={
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME"),
    }
)
client = instructor.from_openai(base_client, mode=instructor.Mode.JSON)

@traceable(name="TaxSentinel_Validator")
async def validate_retrieval(query: str, context: str) -> RelevanceResult:
    """
    Checks if the retrieved legal context is actually relevant to the audit query.
    """
    return await client.chat.completions.create(
        model="meta-llama/llama-3.2-3b-instruct", # Use a fast/cheap model for validation
        response_model=RelevanceResult,
        messages=[
            {"role": "system", "content": "You are a legal search validator. Check if the provided Context contains laws relevant to the Query."},
            {"role": "user", "content": f"Query: {query}\n\nContext: {context}"}
        ]
    )
