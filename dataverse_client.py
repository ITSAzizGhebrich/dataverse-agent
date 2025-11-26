# dataverse_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DATAVERSE_URL = os.getenv("DATAVERSE_URL")
TENANT_ID     = os.getenv("DATAVERSE_TENANT_ID")
CLIENT_ID     = os.getenv("DATAVERSE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

_token_cache = None
_token_expiry = 0.0  # timestamp


def get_dataverse_token() -> str:
    global _token_cache, _token_expiry

    now = time.time()
    # Si on a déjà un token valide, on le réutilise
    if _token_cache is not None and now < _token_expiry - 60:
        return _token_cache

    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": f"{DATAVERSE_URL}/.default"
    }

    r = requests.post(url, data=data, timeout=30)
    r.raise_for_status()
    payload = r.json()

    access_token = payload["access_token"]
    expires_in = payload.get("expires_in", 3600)  # en secondes

    _token_cache = access_token
    _token_expiry = now + int(expires_in)

    return _token_cache


def dataverse_get(relative_url: str):
    token = get_dataverse_token()
    url = f"{DATAVERSE_URL}/api/data/v9.2/{relative_url.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()
