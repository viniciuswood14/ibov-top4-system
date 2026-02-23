from __future__ import annotations
import os
import requests

SERVICE_URL = os.getenv("SERVICE_URL", "").rstrip("/")

def main():
    if not SERVICE_URL:
        raise RuntimeError("Defina SERVICE_URL com a URL pública do seu Web Service (Render). Ex: https://seuapp.onrender.com")
    r = requests.post(f"{SERVICE_URL}/snapshot/run", timeout=180)
    r.raise_for_status()
    print("OK:", r.json())

if __name__ == "__main__":
    main()
