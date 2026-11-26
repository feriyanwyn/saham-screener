"""AI Trading Decision Engine.
Menggabungkan data pasar, indikator teknikal, model Deep Learning, LLM quantitative reasoning,
dan rule-based validator gatekeeper.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from src.ai_assistant.llm_provider import BaseLLMProvider, get_llm_provider
from src.ai_assistant.prompts import (
    SYSTEM_PROMPT_ANALYST,
    build_single_stock_analysis_prompt,
    build_multi_stock_ranking_prompt
)
from src.ai_assistant.validator import AIDecisionValidator
from src.technical_analysis.indicators import TechnicalAnalysisEngine
from src.machine_learning.trainer import ModelPipeline
from config.idx_constants import get_ara_arb_limits


class AITradingDecisionEngine:
    """End-to-end AI Decision Engine combining Quantitative Analytics & LLM Reasoning."""

    def __init__(
        self, 
        llm_provider: Optional[BaseLLMProvider] = None,
        ml_pipeline: Optional[ModelPipeline] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.ml_pipe = ml_pipeline or ModelPipeline()

    def analyze_stock(
        self,
        ticker: str,
        df_candles: pd.DataFrame,
        quote: Optional[Dict[str, Any]] = None,
        timeframe: str = "5M"
    ) -> Dict[str, Any]:
        """Melakukan analisis komprehensif saham tunggal dengan LLM dan memvalidasi hasilnya."""
        if df_candles.empty or len(df_candles) < 20:
            return {
                "stock_ticker": ticker,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "decision": "NO TRADE",
                "validation_status": "REJECTED",
                "rejection_reason": "Insufficient intraday data points for reliable analysis.",
                "detailed_explanation": "Data candle tidak memadai untuk mengevaluasi indikator teknikal dan model Deep Learning."
            }

        # 1. Hitung Indikator Teknikal
        df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_candles)
        ta = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
        last_price = ta["close"]
        prev_close = quote.get("previous_close", df_candles["close"].iloc[0]) if quote else df_candles["close"].iloc[0]

        # 2. Ambil Prediksi Deep Learning
        ml_pred = self.ml_pipe.predict_latest(df_ta, ticker=ticker, timeframe=timeframe)

        # 3. Hitung Batas ARA / ARB
        ara_price, arb_price = get_ara_arb_limits(prev_close)

        # 4. Susun Payload Data Lengkap
        market_payload = {
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
            "last_price": last_price,
            "open": float(df_candles["open"].iloc[-1]),
            "high": float(df_candles["high"].iloc[-1]),
            "low": float(df_candles["low"].iloc[-1]),
            "previous_close": prev_close,
            "change_pct": round(((last_price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0,
            "volume": int(df_candles["volume"].iloc[-1]),
            "value": quote.get("value", last_price * int(df_candles["volume"].iloc[-1])) if quote else last_price * int(df_candles["volume"].iloc[-1]),
            "relative_volume": ta.get("relative_volume", 1.0),
            "spread_ticks": quote.get("spread_ticks", 1) if quote else 1,
            "best_bid": quote.get("bid", last_price) if quote else last_price,
            "best_ask": quote.get("ask", last_price) if quote else last_price,
            "rsi_14": ta.get("rsi_14"),
            "macd": ta.get("macd"),
            "macd_signal": ta.get("macd_signal"),
            "macd_hist": ta.get("macd_hist"),
            "is_macd_bullish": ta.get("is_macd_bullish"),
            "ema_9": ta.get("ema_9"),
            "ema_20": ta.get("ema_20"),
            "ema_50": ta.get("ema_50"),
            "vwap": ta.get("vwap"),
            "is_above_vwap": ta.get("is_above_vwap"),
            "atr_14": ta.get("atr_14"),
            "lstm_predicted_return": ml_pred.get("predicted_return"),
            "bilstm_direction_prob": ml_pred.get("up_probability"),
            "calibrated_confidence": ml_pred.get("calibrated_confidence"),
            "ara_price": ara_price,
            "arb_price": arb_price
        }

        # 5. Kirim ke LLM
        prompt = build_single_stock_analysis_prompt(market_payload)
        try:
            raw_ai_res = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT_ANALYST)
        except Exception as e:
            raw_ai_res = {
                "decision": "HOLD",
                "detailed_explanation": f"LLM Inference Fallback: {e}"
            }

        # Pastikan field dasar ada
        raw_ai_res["stock_ticker"] = ticker
        raw_ai_res["analysis_timestamp"] = market_payload["timestamp"]

        # 6. Jalankan Rule-Based Validator Gatekeeper
        final_decision = AIDecisionValidator.validate_recommendation(raw_ai_res, market_payload)
        return final_decision

    def rank_screened_stocks(self, screened_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Menyusun ranking multi-saham hasil screening menggunakan analisis LLM."""
        if not screened_stocks:
            return {"ranking": [], "top_pick": None, "market_summary": "Tidak ada saham dalam daftar screening."}

        prompt = build_multi_stock_ranking_prompt(screened_stocks[:15])
        try:
            res = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT_ANALYST)
            return res
        except Exception as e:
            return {
                "ranking": [],
                "top_pick": screened_stocks[0]["ticker"] if screened_stocks else None,
                "market_summary": f"Fallback pemeringkatan kuantitatif: {e}"
            }
