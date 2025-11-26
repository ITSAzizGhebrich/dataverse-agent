# llm_client.py
import os
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE_URL  = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")


class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("❌ GEMINI_API_KEY is missing from .env")

        self.url = f"{GEMINI_BASE_URL}/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    def chat(self, system: str, user: str) -> str:
        """
        Compatible Gemini 2.x : un seul message 'user'
        Le prompt system est concaténé dans le message final.
        """

        final_prompt = system.strip() + "\n\n" + user.strip()

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": final_prompt}
                    ]
                }
            ]
        }

        logger.info("📨 Envoi requête vers Gemini...")

        resp = requests.post(self.url, json=payload)
        if resp.status_code != 200:
            logger.error(f"❌ Gemini Error {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        data = resp.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            logger.error(f"Réponse Gemini inattendue : {data}")
            return str(data)


# Instance globale
llm_client = GeminiClient()
