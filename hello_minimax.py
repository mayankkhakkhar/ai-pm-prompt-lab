"""First call to MiniMax API.

Verifies your API key works and you can make a basic chat completion.
This is your Day 1 sanity check — if this runs, the rest of Phase 1 can build on it.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url=os.environ.get("MINIMAX_BASE_URL", "https://api.MiniMax.chat/v1"),
)

model = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "Say hello in exactly 5 words."},
    ],
    temperature=0.7,
    max_tokens=100,
)

print(f"Model:    {model}")
print(f"Usage:    prompt={response.usage.prompt_tokens} "
      f"completion={response.usage.completion_tokens} "
      f"total={response.usage.total_tokens}")
print(f"Response: {response.choices[0].message.content}")