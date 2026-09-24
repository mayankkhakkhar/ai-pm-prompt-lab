"""First call to Google Gemini API.

Verifies your Gemini API key works alongside MiniMax. Same pattern, different surface area.
"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

response = client.models.generate_content(
    model=model,
    contents="Say hello in exactly 5 words.",
)

print(f"Model:    {model}")
print(f"Response: {response.text}")