"""Abstract Base Data Provider for Indonesian Stock Market (IDX)."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import pandas as pd


class BaseDataProvider(ABC):
    """Abstract interface defining required market data operations for IDX."""

    @abstractmethod
    def get_instruments(self) -> List[Dict[str, Any]]:
        """Mengambil seluruh daftar instrumen saham BEI."""
        pass

    @abstractmethod
    def get_daily_history(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Mengambil data historis harian OHLCV."""
        pass

    @abstractmethod
    def get_intraday_data(
        self, 
        ticker: str, 
        timeframe: str = "5m", 
        limit: int = 100
    ) -> pd.DataFrame:
        """Mengambil data candle intraday (1m, 5m, 15m, 1h)."""
        pass

    @abstractmethod
    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        """Mengambil harga snapshot terkini suatu saham."""
        pass

    @abstractmethod
    def get_order_book(self, ticker: str) -> Dict[str, Any]:
        """Mengambil data antrean bid-ask (Market Depth)."""
        pass
