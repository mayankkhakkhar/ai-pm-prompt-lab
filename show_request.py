"""Show what gets sent to MiniMax on a typical call.

Educational — doesn't make a real API call. Just shows the HTTP request
structure (URL, headers, body) so you understand what's on the wire.

Run: python show_request.py
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("MINIMAX_API_KEY", "<not set>")
base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
model = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")

# Mask the key for display — never log full secrets
if len(api_key) >= 12 and api_key != "<not set>":
    masked_key = api_key[:7] + "..." + api_key[-4:]
else:
    masked_key = "<not set or too short>"

# The endpoint, headers, body — exactly what the OpenAI SDK constructs
endpoint = f"{base_url}/chat/completions"
headers = {
    "Authorization": f"Bearer {masked_key}",
    "Content-Type": "application/json",
}
body = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "Say hello in exactly 5 words."},
    ],
    "temperature": 0.7,
    "max_tokens": 100,
}

print("=" * 60)
print(f"POST {endpoint}")
print("=" * 60)

print("\nHeaders:")
for k, v in headers.items():
    print(f"  {k}: {v}")

print("\nBody (JSON):")
print(json.dumps(body, indent=2))

print()
print("=" * 60)
print("Cost-relevant fields:")
print(f"  model:       {model}  (M2.7 is the cheapest reasoning-capable model)")
print(f"  temperature: {body['temperature']}  (0 = deterministic, 1 = creative)")
print(f"  max_tokens:  {body['max_tokens']}  (cap on completion length, not prompt)")
print("=" * 60)

print("\nIf you want to send this for real, run: python hello_minimax.py")