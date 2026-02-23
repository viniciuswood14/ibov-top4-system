import re, requests
from bs4 import BeautifulSoup

B3_IBOV_URL = "https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-composicao-da-carteira.htm"

def fetch_ibov_tickers(timeout: int = 30) -> list[str]:
    html = requests.get(B3_IBOV_URL, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"}).text
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    cands = set(re.findall(r"\b[A-Z]{4}\d{1,2}\b", text))
    return sorted([t for t in cands if len(t) in (5,6)])
