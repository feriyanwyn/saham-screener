"""Unit tests for Technical Analysis Engine."""
import numpy as np
import pandas as pd
from src.technical_analysis.indicators import TechnicalAnalysisEngine


def sample_ohlcv():
    dates = pd.date_range("2026-01-01", periods=50, freq="5min")
    close = np.linspace(1000, 1100, 50) + np.sin(np.linspace(0, 10, 50)) * 20
    df = pd.DataFrame({
        "timestamp": dates,
        "open": close - 2,
        "high": close + 5,
        "low": close - 5,
        "close": close,
        "volume": np.random.randint(10000, 50000, 50)
    })
    return df


def test_rsi_calculation(sample_ohlcv):
    rsi = TechnicalAnalysisEngine.calculate_rsi(sample_ohlcv["close"], period=14)
    assert len(rsi) == len(sample_ohlcv)
    assert 0 <= rsi.iloc[-1] <= 100


def test_macd_calculation(sample_ohlcv):
    macd, signal, hist = TechnicalAnalysisEngine.calculate_macd(sample_ohlcv["close"])
    assert len(macd) == len(sample_ohlcv)
    assert len(signal) == len(sample_ohlcv)
    assert len(hist) == len(sample_ohlcv)


def test_apply_all_indicators(sample_ohlcv):
    enriched = TechnicalAnalysisEngine.apply_all_indicators(sample_ohlcv)
    expected_cols = [
        "ema_9", "ema_20", "ema_50", "rsi_14", "macd", "macd_signal",
        "macd_hist", "atr_14", "bb_middle", "bb_upper", "bb_lower",
        "vwap", "volume_ma_20", "relative_volume"
    ]
    for col in expected_cols:
        assert col in enriched.columns
