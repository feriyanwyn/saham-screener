"""Technical Analysis Engine for Indonesian Stock Market (IDX).
Mengimplementasikan perhitungan indikator teknikal murni dengan NumPy & Pandas.
Mencakup RSI, MACD, EMA (9, 20, 50), VWAP, ATR, Bollinger Bands, Volume MA, dan Relative Volume.
"""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


class TechnicalAnalysisEngine:
    """Vectorized Technical Analysis Indicator Engine."""

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Menghitung Relative Strength Index (RSI 14) dengan smoothed exponential approach (Wilder)."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0.0)).copy()
        loss = (-delta.where(delta < 0, 0.0)).copy()

        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0).round(2)

    @staticmethod
    def calculate_ema(series: pd.Series, span: int) -> pd.Series:
        """Exponential Moving Average (EMA)."""
        return series.ewm(span=span, adjust=False).mean().round(2)

    @staticmethod
    def calculate_macd(
        series: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Menghitung MACD line, Signal line, dan Histogram."""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = (ema_fast - ema_slow).round(2)
        signal_line = macd_line.ewm(span=signal, adjust=False).mean().round(2)
        histogram = (macd_line - signal_line).round(2)
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Menghitung Average True Range (ATR 14)."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        return atr.bfill().round(2)

    @staticmethod
    def calculate_bollinger_bands(
        series: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands (Middle, Upper, Lower)."""
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = (middle + (std * std_dev)).round(2)
        lower = (middle - (std * std_dev)).round(2)
        return middle.round(2), upper, lower

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price (VWAP)."""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        cum_volume = df["volume"].cumsum()
        cum_value = (typical_price * df["volume"]).cumsum()
        vwap = cum_value / cum_volume.replace(0, np.nan)
        return vwap.ffill().round(2)

    @classmethod
    def apply_all_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Memperkaya DataFrame OHLCV dengan seluruh indikator teknikal."""
        if df.empty or len(df) < 5:
            return df

        data = df.copy()
        
        # 1. Moving Averages
        data["ema_9"] = cls.calculate_ema(data["close"], span=9)
        data["ema_20"] = cls.calculate_ema(data["close"], span=20)
        data["ema_50"] = cls.calculate_ema(data["close"], span=50)

        # 2. RSI 14
        data["rsi_14"] = cls.calculate_rsi(data["close"], period=14)

        # 3. MACD
        macd, signal, hist = cls.calculate_macd(data["close"])
        data["macd"] = macd
        data["macd_signal"] = signal
        data["macd_hist"] = hist

        # 4. ATR 14
        data["atr_14"] = cls.calculate_atr(data, period=14)

        # 5. Bollinger Bands
        bb_mid, bb_upper, bb_lower = cls.calculate_bollinger_bands(data["close"])
        data["bb_middle"] = bb_mid
        data["bb_upper"] = bb_upper
        data["bb_lower"] = bb_lower

        # 6. VWAP
        if "vwap" not in data.columns or data["vwap"].isna().all():
            data["vwap"] = cls.calculate_vwap(data)

        # 7. Volume Moving Average & Relative Volume
        data["volume_ma_20"] = data["volume"].rolling(window=20).mean().bfill()
        data["relative_volume"] = (data["volume"] / data["volume_ma_20"].replace(0, np.nan)).fillna(1.0).round(2)

        # 8. Crossover & Pattern Flags
        data["golden_cross"] = (data["ema_20"] > data["ema_50"]) & (data["ema_20"].shift(1) <= data["ema_50"].shift(1))
        data["death_cross"] = (data["ema_20"] < data["ema_50"]) & (data["ema_20"].shift(1) >= data["ema_50"].shift(1))
        data["macd_bullish_cross"] = (data["macd"] > data["macd_signal"]) & (data["macd"].shift(1) <= data["macd_signal"].shift(1))
        data["macd_bearish_cross"] = (data["macd"] < data["macd_signal"]) & (data["macd"].shift(1) >= data["macd_signal"].shift(1))
        data["above_vwap"] = data["close"] > data["vwap"]
        data["volume_spike"] = data["relative_volume"] >= 1.5

        return data

    @classmethod
    def get_latest_signals_summary(cls, df_with_indicators: pd.DataFrame) -> Dict[str, Any]:
        """Menganalisis kondisi teknikal pada candle penutupan terakhir."""
        if df_with_indicators.empty:
            return {}

        latest = df_with_indicators.iloc[-1]
        prev = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else latest

        return {
            "close": float(latest["close"]),
            "rsi_14": float(latest.get("rsi_14", 50.0)),
            "is_rsi_oversold": bool(latest.get("rsi_14", 50.0) < 30),
            "is_rsi_overbought": bool(latest.get("rsi_14", 50.0) > 70),
            "macd": float(latest.get("macd", 0.0)),
            "macd_signal": float(latest.get("macd_signal", 0.0)),
            "macd_hist": float(latest.get("macd_hist", 0.0)),
            "is_macd_bullish": bool(latest.get("macd", 0.0) > latest.get("macd_signal", 0.0)),
            "macd_crossover": bool(latest.get("macd_bullish_cross", False)),
            "ema_9": float(latest.get("ema_9", 0.0)),
            "ema_20": float(latest.get("ema_20", 0.0)),
            "ema_50": float(latest.get("ema_50", 0.0)),
            "is_uptrend": bool(latest.get("ema_20", 0.0) > latest.get("ema_50", 0.0)),
            "vwap": float(latest.get("vwap", latest["close"])),
            "is_above_vwap": bool(latest["close"] > latest.get("vwap", latest["close"])),
            "atr_14": float(latest.get("atr_14", 0.0)),
            "relative_volume": float(latest.get("relative_volume", 1.0)),
            "is_volume_spike": bool(latest.get("relative_volume", 1.0) >= 1.5)
        }
