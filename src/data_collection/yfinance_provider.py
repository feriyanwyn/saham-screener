"""Yahoo Finance Data Provider for IDX Stocks (.JK).
Digunakan sebagai fallback gratis, data historis jangka panjang, dan prototyping.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import yfinance as yf
from src.data_collection.base_provider import BaseDataProvider
from config.idx_constants import align_to_tick, get_tick_size


class YahooFinanceProvider(BaseDataProvider):
    """Provider data menggunakan yfinance dengan konversi otomatis ticker ke format BEI (.JK)."""

    def __init__(self):
        self.popular_idx_tickers = [
            {"ticker": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Financials", "board": "Utama"},
            {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "sector": "Financials", "board": "Utama"},
            {"ticker": "BMRI", "name": "Bank Mandiri Tbk", "sector": "Financials", "board": "Utama"},
            {"ticker": "BBNI", "name": "Bank Negara Indonesia Tbk", "sector": "Financials", "board": "Utama"},
            {"ticker": "TLKM", "name": "Telkom Indonesia Tbk", "sector": "Telecommunication", "board": "Utama"},
            {"ticker": "ASII", "name": "Astra International Tbk", "sector": "Industrials", "board": "Utama"},
            {"ticker": "UNVR", "name": "Unilever Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "board": "Utama"},
            {"ticker": "ICBP", "name": "Indofood CBP Sukses Makmur Tbk", "sector": "Consumer Non-Cyclicals", "board": "Utama"},
            {"ticker": "INDF", "name": "Indofood Sukses Makmur Tbk", "sector": "Consumer Non-Cyclicals", "board": "Utama"},
            {"ticker": "ADRO", "name": "Adaro Energy Indonesia Tbk", "sector": "Energy", "board": "Utama"},
            {"ticker": "PTBA", "name": "Bukit Asam Tbk", "sector": "Energy", "board": "Utama"},
            {"ticker": "PGAS", "name": "Perusahaan Gas Negara Tbk", "sector": "Energy", "board": "Utama"},
            {"ticker": "ANTM", "name": "Aneka Tambang Tbk", "sector": "Basic Materials", "board": "Utama"},
            {"ticker": "INCO", "name": "Vale Indonesia Tbk", "sector": "Basic Materials", "board": "Utama"},
            {"ticker": "MDKA", "name": "Merdeka Copper Gold Tbk", "sector": "Basic Materials", "board": "Utama"},
            {"ticker": "BRIS", "name": "Bank Syariah Indonesia Tbk", "sector": "Financials", "board": "Utama"},
            {"ticker": "GOTO", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Technology", "board": "Pengembangan"},
            {"ticker": "BUKA", "name": "Bukalapak.com Tbk", "sector": "Technology", "board": "Pengembangan"},
            {"ticker": "AMMN", "name": "Amman Mineral Internasional Tbk", "sector": "Basic Materials", "board": "Utama"},
            {"ticker": "BREN", "name": "Barito Renewables Energy Tbk", "sector": "Energy", "board": "Utama"},
            {"ticker": "TPIA", "name": "Chandra Asri Pacific Tbk", "sector": "Basic Materials", "board": "Utama"},
            {"ticker": "MEDC", "name": "Medco Energi Internasional Tbk", "sector": "Energy", "board": "Utama"},
            {"ticker": "KLBF", "name": "Kalbe Farma Tbk", "sector": "Healthcare", "board": "Utama"},
            {"ticker": "CPIN", "name": "Charoen Pokphand Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "board": "Utama"},
            {"ticker": "JPFA", "name": "Japfa Comfeed Indonesia Tbk", "sector": "Consumer Non-Cyclicals", "board": "Utama"},
        ]

    def _format_ticker(self, ticker: str) -> str:
        clean = ticker.upper().strip()
        if not clean.endswith(".JK"):
            return f"{clean}.JK"
        return clean

    def _strip_ticker(self, ticker: str) -> str:
        return ticker.upper().replace(".JK", "").strip()

    def get_instruments(self) -> List[Dict[str, Any]]:
        return [
            {
                "ticker": item["ticker"],
                "name": item["name"],
                "sector": item["sector"],
                "industry": item.get("sector", "General"),
                "board": item["board"],
                "is_active": True,
                "is_suspended": False
            }
            for item in self.popular_idx_tickers
        ]

    def get_daily_history(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        formatted = self._format_ticker(ticker)
        start = start_date or (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
        end = end_date or datetime.utcnow().strftime("%Y-%m-%d")

        try:
            df = yf.download(formatted, start=start, end=end, progress=False)
            if df.empty:
                return pd.DataFrame()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0].lower() for col in df.columns]
            else:
                df.columns = [str(col).lower() for col in df.columns]

            df = df.reset_index()
            date_col = "date" if "date" in df.columns else "datetime"
            df.rename(columns={date_col: "timestamp"}, inplace=True)
            
            if "value" not in df.columns:
                df["value"] = df["close"] * df["volume"]
                
            return df[["timestamp", "open", "high", "low", "close", "volume", "value"]].dropna()
        except Exception as e:
            print(f"[YahooFinanceProvider] Error fetching daily history for {ticker}: {e}")
            return pd.DataFrame()

    def get_intraday_data(
        self, 
        ticker: str, 
        timeframe: str = "5m", 
        limit: int = 100
    ) -> pd.DataFrame:
        formatted = self._format_ticker(ticker)
        valid_intervals = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d"}
        interval = timeframe.lower()
        period = valid_intervals.get(interval, "5d")

        try:
            df = yf.download(formatted, interval=interval, period=period, progress=False)
            if df.empty:
                return pd.DataFrame()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0].lower() for col in df.columns]
            else:
                df.columns = [str(col).lower() for col in df.columns]

            df = df.reset_index()
            date_col = "datetime" if "datetime" in df.columns else "date"
            df.rename(columns={date_col: "timestamp"}, inplace=True)
            
            if "value" not in df.columns:
                df["value"] = df["close"] * df["volume"]
            
            cum_vol = df["volume"].cumsum()
            cum_val = (df["close"] * df["volume"]).cumsum()
            df["vwap"] = (cum_val / cum_vol.replace(0, 1)).round(2)

            return df.tail(limit).reset_index(drop=True)
        except Exception as e:
            print(f"[YahooFinanceProvider] Error fetching intraday data for {ticker}: {e}")
            return pd.DataFrame()

    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        formatted = self._format_ticker(ticker)
        try:
            t = yf.Ticker(formatted)
            fast_info = getattr(t, "fast_info", None)
            if fast_info:
                last_price = float(fast_info.get("lastPrice", 0.0))
                prev_close = float(fast_info.get("previousClose", last_price))
                open_price = float(fast_info.get("open", last_price))
                high_price = float(fast_info.get("dayHigh", last_price))
                low_price = float(fast_info.get("dayLow", last_price))
                volume = int(fast_info.get("lastVolume", 0))
            else:
                hist = t.history(period="1d")
                if hist.empty:
                    return {}
                last_price = float(hist["Close"].iloc[-1])
                open_price = float(hist["Open"].iloc[-1])
                high_price = float(hist["High"].iloc[-1])
                low_price = float(hist["Low"].iloc[-1])
                prev_close = open_price
                volume = int(hist["Volume"].iloc[-1])

            change = last_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0.0

            return {
                "ticker": self._strip_ticker(ticker),
                "last_price": align_to_tick(last_price),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "previous_close": prev_close,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": volume,
                "value": volume * last_price,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"[YahooFinanceProvider] Error fetching live quote for {ticker}: {e}")
            return {}

    def get_order_book(self, ticker: str) -> Dict[str, Any]:
        quote = self.get_live_quote(ticker)
        if not quote or quote.get("last_price", 0) <= 0:
            return {"ticker": self._strip_ticker(ticker), "bids": [], "asks": []}

        last = quote["last_price"]
        tick = get_tick_size(last)
        
        bids = [{"price": max(1, last - (i * tick)), "lot": 250 - (i * 30), "orders": 15 - i} for i in range(1, 6)]
        asks = [{"price": last + (i * tick), "lot": 200 + (i * 25), "orders": 12 + i} for i in range(1, 6)]

        return {"ticker": self._strip_ticker(ticker), "bids": bids, "asks": asks}
