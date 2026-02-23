from dataclasses import dataclass
import requests
from .utils import chunks
BASE_URL = "https://brapi.dev/api"

@dataclass(frozen=True)
class BrapiClient:
    token: str
    timeout: int = 30
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    def quote_with_history(self, tickers, range_="2y", interval="1d"):
        results = []
        for group in chunks(tickers, 40):
            r = requests.get(f"{BASE_URL}/quote/{','.join(group)}", params={"range":range_,"interval":interval}, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            results.extend(r.json().get("results", []))
        return results
    def quote_with_modules(self, tickers, modules="defaultKeyStatistics,financialData,summaryProfile"):
        results = []
        for group in chunks(tickers, 20):
            r = requests.get(f"{BASE_URL}/quote/{','.join(group)}", params={"modules":modules}, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            results.extend(r.json().get("results", []))
        return results
