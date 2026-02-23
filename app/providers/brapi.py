from __future__ import annotations
import requests
from dataclasses import dataclass
from typing import Any
from .utils import chunks

BASE_URL = "https://brapi.dev/api"

@dataclass(frozen=True)
class BrapiClient:
    token: str
    timeout: int = 30

    def _headers(self) -> dict[str,str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def quote_with_history(self, tickers: list[str], range_: str = "2y", interval: str = "1d") -> list[dict[str,Any]]:
        results: list[dict[str,Any]] = []
        for group in chunks(tickers, 40):
            url = f"{BASE_URL}/quote/{','.join(group)}"
            params = {"range": range_, "interval": interval}
            r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            results.extend(r.json().get("results", []))
        return results

    def quote_with_modules(self, tickers: list[str], modules: str = "defaultKeyStatistics,financialData,summaryProfile") -> list[dict[str,Any]]:
        results: list[dict[str,Any]] = []
        for group in chunks(tickers, 20):
            url = f"{BASE_URL}/quote/{','.join(group)}"
            params = {"modules": modules}
            r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            results.extend(r.json().get("results", []))
        return results
