"""Stock Screener Engine for Indonesian Stock Exchange (IDX)."""
from typing import List, Dict, Any
import pandas as pd
from config.idx_constants import get_tick_size
from src.data_collection.base_provider import BaseDataProvider
from src.technical_analysis.indicators import TechnicalAnalysisEngine


class StockScreener:
    """Multi-factor quantitative stock screener for IDX."""

    def __init__(self, provider: BaseDataProvider):
        self.provider = provider

    def screen_stocks(
        self,
        min_value_idr: float = 1_000_000_000.0,
        min_rel_volume: float = 1.0,
        max_spread_ticks: int = 3,
        min_price: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Memindai seluruh instrumen aktif dan memberikan ranking peluang scalping."""
        instruments = self.provider.get_instruments()
        screened_results = []

        for inst in instruments:
            ticker = inst["ticker"]
            if not inst.get("is_active", True) or inst.get("is_suspended", False):
                continue

            quote = self.provider.get_live_quote(ticker)
            if not quote or quote.get("last_price", 0) < min_price:
                continue

            last_price = quote["last_price"]
            value = quote.get("value", 0.0)

            if value < min_value_idr:
                continue

            ob = self.provider.get_order_book(ticker)
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            if not bids or not asks:
                continue

            best_bid = bids[0]["price"]
            best_ask = asks[0]["price"]
            tick = get_tick_size(last_price)
            spread_ticks = int(round((best_ask - best_bid) / max(1, tick)))
            if spread_ticks > max_spread_ticks:
                continue

            df_intraday = self.provider.get_intraday_data(ticker, timeframe="5m", limit=60)
            if df_intraday.empty or len(df_intraday) < 15:
                continue

            df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_intraday)
            ta_summary = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
            rel_vol = ta_summary.get("relative_volume", 1.0)
            if rel_vol < min_rel_volume:
                continue

            # Multi-factor Opportunity Scoring (0 - 100)
            score = 0.0
            rsi = ta_summary.get("rsi_14", 50.0)
            if 45 <= rsi <= 65:
                score += 25.0
            elif 35 <= rsi < 45:
                score += 15.0

            if ta_summary.get("is_macd_bullish", False):
                score += 20.0
            if ta_summary.get("macd_crossover", False):
                score += 15.0
            if ta_summary.get("is_above_vwap", False):
                score += 20.0
            if rel_vol >= 1.5:
                score += 20.0

            score = min(100.0, score)

            if ta_summary.get("is_uptrend") and ta_summary.get("is_above_vwap"):
                trend_status = "BULLISH_MOMENTUM"
            elif ta_summary.get("is_uptrend"):
                trend_status = "UPTREND"
            elif not ta_summary.get("is_above_vwap") and rsi < 45:
                trend_status = "BEARISH"
            else:
                trend_status = "SIDEWAYS"

            screened_results.append({
                "ticker": ticker,
                "name": inst.get("name", ticker),
                "sector": inst.get("sector", "General"),
                "board": inst.get("board", "Utama"),
                "last_price": last_price,
                "change_pct": quote.get("change_pct", 0.0),
                "volume": quote.get("volume", 0),
                "value": value,
                "bid": best_bid,
                "ask": best_ask,
                "spread_ticks": spread_ticks,
                "relative_volume": rel_vol,
                "rsi_14": rsi,
                "macd": ta_summary.get("macd", 0.0),
                "vwap": ta_summary.get("vwap", last_price),
                "atr_14": ta_summary.get("atr_14", 0.0),
                "trend_status": trend_status,
                "opportunity_score": round(score, 1)
            })

        screened_results.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return screened_results
