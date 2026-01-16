import os
import json
import time
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from app.utils.pdf_processor import extract_text_from_pdf

load_dotenv()

# Define the structure for the extracted rates
class HSNRate(BaseModel):
    hsn_code: str = Field(..., description="The HSN or SAC code (e.g., '9983' or '998311'). Remove spaces/dots.")
    rate: str = Field(..., description="The GST rate tax (e.g., '18%', '5%', 'Nil').")
    description: str = Field(..., description="Short description of the goods or services.")
    legal_ref: str = Field(default="Notification No. 11/2017-Central Tax (Rate)", description="The specific Notification or Act section governing this rate.")

class HSNRateList(BaseModel):
    rates: list[HSNRate]

def extract_rates_to_json():
    pdf_path = "knowledgebase/press_release_press_information_bureau_0.pdf"
    output_path = "app/core/hsn_rates.json"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    print("📖 Extracting text from PDF...")
    # reuse the existing utility
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        print("❌ Failed to extract text.")
        return

    print(f"🤖 Sending {len(raw_text)} chars to Gemini 2.0 Flash (via OpenRouter) for extraction...")

    # OpenRouter Client
    client = instructor.from_openai(
        OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
             default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://taxsentinel.com"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "TaxSentinel"),
            }
        ),
        mode=instructor.Mode.JSON
    )

    # Chunking Strategy
    chunk_size = 5000  # Reduced to avoid max_token limits on output
    chunks = [raw_text[i:i+chunk_size] for i in range(0, len(raw_text), chunk_size)]
    
    rate_map = {}
    
    print(f"🔄 Processing {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        print(f"   Processing chunk {i+1}/{len(chunks)}...")
        retries = 3
        success = False
        
        while retries > 0 and not success:
            try:
                resp = client.chat.completions.create(
                    model="gemini-flash-latest",
                    response_model=HSNRateList,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a data extraction bot. Your job is to convert the raw text of a GST Council Press Release into a structured JSON list of HSN Codes and their Rates. Focus on tables. If a chunk has no rates, return an empty list."
                        },
                        {
                            "role": "user", 
                            "content": f"Extract all HSN/SAC codes and their GST Rates from this text segment. Look for 'HSN', 'Rate', 'Description'. Text:\n\n{chunk}" 
                        }
                    ]
                )
                
                # Aggregate extraction
                if resp.rates:
                    print(f"   Found {len(resp.rates)} items in chunk {i+1}.")
                    for item in resp.rates:
                        clean_hsn = item.hsn_code.replace(" ", "").replace(".", "")
                    if clean_hsn not in rate_map:
                        rate_map[clean_hsn] = []
                    
                    # Avoid duplicates
                    entry = {
                        "rate": item.rate,
                        "description": item.description,
                        "legal_ref": item.legal_ref 
                    }
                    if entry not in rate_map[clean_hsn]:
                        rate_map[clean_hsn].append(entry)
                    print(f"   No items found in chunk {i+1}.")
                
                success = True
                time.sleep(5) # Be kind to API

            except Exception as e:
                print(f"❌ Error extracting chunk {i+1}: {e}. Retrying ({retries-1} left)...")
                retries -= 1
                time.sleep(10)
        
        if not success:
             print(f"❌ Failed to extract chunk {i+1} after all retries.")

    # Save to JSON (Append/Update mode)
    os.makedirs("app/core", exist_ok=True)
    
    existing_data = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass # Start fresh if corrupted
    
    # Merge new rates into existing
    existing_data.update(rate_map)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4)
    
    print(f"✅ Successfully extracted {len(rate_map)} rates. Total Fact Base: {len(existing_data)} entries.")

if __name__ == "__main__":
    extract_rates_to_json()
