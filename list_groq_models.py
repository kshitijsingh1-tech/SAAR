
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv(r"d:\bytebuild\backend\.env")
groq_key = os.getenv("GROQ_API_KEY")

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/models",
    headers={
        "Authorization": f"Bearer {groq_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = [m["id"] for m in data.get("data", [])]
        print("Active Groq models:")
        for m in sorted(models):
            print(" -", m)
except Exception as e:
    print("Error:", e)
