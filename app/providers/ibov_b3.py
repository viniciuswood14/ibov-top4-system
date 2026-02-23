from __future__ import annotations
import re
import requests
from bs4 import BeautifulSoup

B3_IBOV_URL = "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-composicao-da-carteira.htm"

def fetch_ibov_tickers(timeout: int = 30) -> list[str]:
    """Extrai tickers da composição do IBOV a partir da página oficial da B3."""
    html = requests.get(B3_IBOV_URL, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    candidates = set(re.findall(r"\b[A-Z]{4}\d{1,2}\b", text))
    tickers = sorted([t for t in candidates if len(t) in (5, 6)])
    return tickers
