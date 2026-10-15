import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

for model in client.models.list():
    actions = model.supported_actions or []
    if "generateContent" in actions:
        print(model.name)