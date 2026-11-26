"""Mock Data Provider for IDX Stocks.
Digunakan untuk pengujian unit, testing offline, dan simulasi tanpa memakan kuota API eksternal.
Mematuhi aturan fraksi harga BEI, volume realistis, dan order book realistis.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from src.data_collection.base_provider import BaseDataProvider
from config.idx_constants import align_to_tick, get_tick_size


class MockDataProvider(BaseDataProvider):
    """High-fidelity Mock Provider for IDX market simulation."""

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.instruments_data = [
            {"ticker": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Financials", "base_price": 9850, "board": "Utama"},
            {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "sector": "Financials", "base_price": 5200, "board": "Utama"},
            {"ticker": "BMRI", "name": "Bank Mandiri Tbk", "sector": "Financials", "base_price": 6800, "board": "Utama"},
            {"ticker": "TLKM", "name": "Telkom Indonesia Tbk", "sector": "Telecommunication", "base_price": 3150, "board": "Utama"},
            {"ticker": "ASII", "name": "Astra International Tbk", "sector": "Industrials", "base_price": 5100, "board": "Utama"},
            {"ticker": "AMMN", "name": "Amman Mineral Internasional Tbk", "sector": "Basic Materials", "base_price": 10500, "board": "Utama"},
            {"ticker": "ADRO", "name": "Adaro Energy Indonesia Tbk", "sector": "Energy", "base_price": 3650, "board": "Utama"},
            {"ticker": "BREN", "name": "Barito Renewables Energy Tbk", "sector": "Energy", "base_price": 7250, "board": "Utama"},
            {"ticker": "GOTO", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Technology", "base_price": 54, "board": "Pengembangan"},
            {"ticker": "BRIS", "name": "Bank Syariah Indonesia Tbk", "sector": "Financials", "base_price": 2850, "board": "Utama"},
        ]

    def get_instruments(self) -> List[Dict[str, Any]]:
        return [
            {
                "ticker": item["ticker"],
                "name": item["name"],
                "sector": item["sector"],
                "industry": item["sector"],
                "board": item["board"],
                "is_active": True,
                "is_suspended": False
            }
            for item in self.instruments_data
        ]

    def _get_base_price(self, ticker: str) -> float:
        for item in self.instruments_data:
            if item["ticker"] == ticker.upper():
                return item.get("base_price", 1000)
        return 1000.0

    def get_daily_history(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        periods = 180
        base_price = self._get_base_price(ticker)
        dates = pd.date_range(end=datetime.utcnow(), periods=periods, freq="B")
        
        records = []
        current_close = base_price
        for d in dates:
            pct_change = float(np.random.normal(0.001, 0.02))
            new_close = align_to_tick(current_close * (1 + pct_change))
            high_price = align_to_tick(max(current_close, new_close) * (1 + abs(float(np.random.normal(0.005, 0.008)))))
            low_price = align_to_tick(min(current_close, new_close) * (1 - abs(float(np.random.normal(0.005, 0.008)))))
            open_price = align_to_tick(current_close)
            volume = int(abs(np.random.normal(5000000, 1500000)))
            value = volume * new_close
            
            records.append({
                "timestamp": d,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": new_close,
                "volume": volume,
                "value": value
            })
            current_close = new_close

        return pd.DataFrame(records)

    def get_intraday_data(
        self, 
        ticker: str, 
        timeframe: str = "5m", 
        limit: int = 100
    ) -> pd.DataFrame:
        base_price = self._get_base_price(ticker)
        now = datetime.utcnow()
        freq_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}
        freq = freq_map.get(timeframe.lower(), "5min")
        dates = pd.date_range(end=now, periods=limit, freq=freq)

        records = []
        current_close = base_price
        for d in dates:
            pct_change = float(np.random.normal(0.0002, 0.006))
            new_close = align_to_tick(current_close * (1 + pct_change))
            high_price = align_to_tick(max(current_close, new_close) * (1 + abs(float(np.random.normal(0.002, 0.003)))))
            low_price = align_to_tick(min(current_close, new_close) * (1 - abs(float(np.random.normal(0.002, 0.003)))))
            open_price = align_to_tick(current_close)
            volume = int(abs(np.random.normal(80000, 30000)))
            value = volume * new_close
            
            records.append({
                "timestamp": d,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": new_close,
                "volume": volume,
                "value": value
            })
            current_close = new_close

        df = pd.DataFrame(records)
        cum_vol = df["volume"].cumsum()
        cum_val = (df["close"] * df["volume"]).cumsum()
        df["vwap"] = (cum_val / cum_vol.replace(0, 1)).round(2)
        return df

    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        base = self._get_base_price(ticker)
        tick = get_tick_size(base)
        last_price = align_to_tick(base + (int(np.random.randint(-3, 4)) * tick))
        prev_close = base
        change = last_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0.0
        volume = int(abs(np.random.normal(3500000, 500000)))

        return {
            "ticker": ticker.upper(),
            "last_price": last_price,
            "open": base,
            "high": last_price + (2 * tick),
            "low": last_price - (2 * tick),
            "previous_close": prev_close,
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": volume,
            "value": volume * last_price,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_order_book(self, ticker: str) -> Dict[str, Any]:
        quote = self.get_live_quote(ticker)
        last = quote["last_price"]
        tick = get_tick_size(last)

        bids = [
            {"price": max(1, last - (i * tick)), "lot": int(np.random.randint(150, 800)), "orders": int(np.random.randint(10, 45))}
            for i in range(1, 6)
        ]
        asks = [
            {"price": last + (i * tick), "lot": int(np.random.randint(150, 800)), "orders": int(np.random.randint(10, 45))}
            for i in range(1, 6)
        ]
        return {"ticker": ticker.upper(), "bids": bids, "asks": asks}
