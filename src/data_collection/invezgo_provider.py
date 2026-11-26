"""Invezgo API Data Provider for IDX Stocks.
Dokumentasi: https://api.invezgo.com/documentation
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from src.data_collection.base_provider import BaseDataProvider
from config.settings import settings


class InvezgoProvider(BaseDataProvider):
    """Invezgo API integration layer with Bearer Token auth."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.INVEZGO_API_KEY
        self.base_url = (base_url or settings.INVEZGO_BASE_URL).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            print(f"[InvezgoProvider] Request error {url}: {e}")
            return None

    def get_instruments(self) -> List[Dict[str, Any]]:
        data = self._get("/api/v1/instruments")
        if not data or "data" not in data:
            return []
        
        instruments = []
        for item in data["data"]:
            instruments.append({
                "ticker": item.get("symbol", "").upper(),
                "name": item.get("name", ""),
                "sector": item.get("sector", ""),
                "industry": item.get("industry", ""),
                "board": item.get("board", "Utama"),
                "is_active": item.get("is_active", True),
                "is_suspended": item.get("is_suspended", False)
            })
        return instruments

    def get_daily_history(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        params = {"symbol": ticker.upper()}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        data = self._get("/api/v1/chart/daily", params=params)
        if not data or "candles" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["candles"])
        return df

    def get_intraday_data(
        self, 
        ticker: str, 
        timeframe: str = "5m", 
        limit: int = 100
    ) -> pd.DataFrame:
        params = {"symbol": ticker.upper(), "interval": timeframe, "limit": limit}
        data = self._get("/api/v1/chart/intraday", params=params)
        if not data or "candles" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["candles"])
        return df

    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        data = self._get(f"/api/v1/quote/{ticker.upper()}")
        if not data or "quote" not in data:
            return {}
        return data["quote"]

    def get_order_book(self, ticker: str) -> Dict[str, Any]:
        data = self._get(f"/api/v1/market-depth/{ticker.upper()}")
        if not data:
            return {"ticker": ticker.upper(), "bids": [], "asks": []}
        return {
            "ticker": ticker.upper(),
            "bids": data.get("bids", []),
            "asks": data.get("asks", [])
        }
