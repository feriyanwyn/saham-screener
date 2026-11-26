"""Api.co.id Data Provider for IDX Stocks.
Dokumentasi: https://api.co.id/api-saham-indonesia/
"""
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from src.data_collection.base_provider import BaseDataProvider
from config.settings import settings


class ApiCoIdProvider(BaseDataProvider):
    """Api.co.id integration layer with x-api-co-id header."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.APICOID_API_KEY
        self.base_url = (base_url or settings.APICOID_BASE_URL).rstrip("/")
        self.headers = {
            "x-api-co-id": self.api_key,
            "Accept": "application/json"
        }

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        if not self.api_key:
            return None
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"[ApiCoIdProvider] Request error {url}: {e}")
            return None

    def get_instruments(self) -> List[Dict[str, Any]]:
        data = self._get("/idx/v2/instruments")
        if not data or not data.get("is_success"):
            return []
        
        instruments = []
        for item in data.get("data", []):
            instruments.append({
                "ticker": item.get("symbol", "").upper(),
                "name": item.get("name", ""),
                "sector": item.get("sector", ""),
                "industry": item.get("industry", ""),
                "board": item.get("board", "Utama"),
                "is_active": item.get("status", "ACTIVE") == "ACTIVE",
                "is_suspended": item.get("status", "") == "SUSPENDED"
            })
        return instruments

    def get_daily_history(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        data = self._get(f"/idx/v2/chart/historical/{ticker.upper()}", params={"start": start_date, "end": end_date})
        if not data or not data.get("is_success"):
            return pd.DataFrame()
        return pd.DataFrame(data.get("data", []))

    def get_intraday_data(
        self, 
        ticker: str, 
        timeframe: str = "5m", 
        limit: int = 100
    ) -> pd.DataFrame:
        data = self._get(f"/idx/v2/chart/intraday/{ticker.upper()}", params={"timeframe": timeframe, "limit": limit})
        if not data or not data.get("is_success"):
            return pd.DataFrame()
        return pd.DataFrame(data.get("data", []))

    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        data = self._get(f"/idx/v2/chart/quote/{ticker.upper()}")
        if not data or not data.get("is_success"):
            return {}
        return data.get("data", {})

    def get_order_book(self, ticker: str) -> Dict[str, Any]:
        data = self._get(f"/idx/v2/live/orderbook/{ticker.upper()}")
        if not data or not data.get("is_success"):
            return {"ticker": ticker.upper(), "bids": [], "asks": []}
        return {
            "ticker": ticker.upper(),
            "bids": data.get("data", {}).get("bids", []),
            "asks": data.get("data", {}).get("asks", [])
        }
