"""Scalping Signal Engine for Indonesian Stock Market (IDX).
Menggabungkan prediksi Machine Learning (LSTM & BiLSTM) dengan indikator teknikal.
Menghasilkan status BUY, SELL, HOLD, dan WATCHLIST dengan validasi fraksi harga, ARA/ARB, dan friksi biaya.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from config.idx_constants import align_to_tick, get_tick_size, get_ara_arb_limits
from config.settings import settings
from src.technical_analysis.indicators import TechnicalAnalysisEngine
from src.machine_learning.trainer import ModelPipeline


class ScalpingSignalEngine:
    """Ensemble quantitative signal engine with strict risk & market validation."""

    def __init__(self, ml_pipeline: Optional[ModelPipeline] = None):
        self.ml_pipeline = ml_pipeline or ModelPipeline()

    def generate_signal(
        self, 
        df_candles: pd.DataFrame, 
        ticker: str, 
        timeframe: str = "5M",
        prev_close: Optional[float] = None
    ) -> Dict[str, Any]:
        """Menganalisis data pasar dan menghasilkan sinyal trading terstruktur."""
        if df_candles.empty or len(df_candles) < 25:
            return {
                "ticker": ticker,
                "signal_type": "HOLD",
                "rationale": "Insufficient data points for analysis.",
                "confidence": 0.0
            }

        # 1. Hitung Indikator Teknikal
        df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_candles)
        ta = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
        last_price = ta["close"]
        tick = get_tick_size(last_price)
        p_close = prev_close or df_candles["close"].iloc[0]

        # 2. Cek Batas ARA / ARB
        ara_price, arb_price = get_ara_arb_limits(p_close)
        is_near_ara = (ara_price - last_price) <= (2 * tick)

        # 3. Prediksi Machine Learning (LSTM return & BiLSTM direction prob)
        ml_pred = self.ml_pipeline.predict_latest(df_ta, ticker=ticker, timeframe=timeframe)
        pred_return = ml_pred.get("predicted_return", 0.0)
        up_prob = ml_pred.get("up_probability", 0.5)
        confidence = ml_pred.get("calibrated_confidence", 0.5)

        # 4. Aturan Logika Scalping Multi-Konfirmasi
        rsi = ta["rsi_14"]
        macd_bullish = ta["is_macd_bullish"]
        above_vwap = ta["is_above_vwap"]
        volume_spike = ta["is_volume_spike"]
        is_uptrend = ta["is_uptrend"]

        # Kondisi BUY:
        # - BiLSTM up_prob > 0.55
        # - LSTM predicted_return > 0.005 (> 0.5%)
        # - RSI dalam rentang momentum (40 - 68, belum overbought ekstrim)
        # - Harga di atas VWAP atau sedang MACD crossover
        # - Tidak mendekati batas ARA
        buy_condition = (
            (up_prob >= 0.55 or pred_return >= 0.006) and
            (40.0 <= rsi <= 68.0) and
            (above_vwap or ta["macd_crossover"]) and
            not is_near_ara
        )

        # Kondisi SELL:
        # - RSI overbought (>75) atau Breakdown di bawah VWAP
        # - Atau BiLSTM up_prob < 0.40 dan MACD bearish cross
        sell_condition = (
            (rsi >= 75.0) or
            (not above_vwap and not macd_bullish and up_prob < 0.42) or
            (ta.get("macd_bearish_cross", False) and rsi < 50.0)
        )

        # Kondisi WATCHLIST:
        # - Volume spike terdeteksi tapi konfirmasi arah belum penuh
        # - Atau RSI oversold (<35) menunggu golden cross
        watchlist_condition = (
            (volume_spike and not above_vwap) or
            (rsi < 35.0 and not sell_condition)
        )

        # 5. Penentuan Level Entry, TP, SL, dan R/R Ratio
        atr = max(float(tick), ta.get("atr_14", float(tick * 2)))

        if buy_condition:
            signal_type = "BUY"
            entry_price = align_to_tick(last_price)
            # Stop loss 1.5 ATR di bawah entry, TP minimal 2.5 ATR di atas entry
            raw_sl = entry_price - (1.5 * atr)
            raw_tp = entry_price + (2.5 * atr)

            stop_loss = align_to_tick(max(float(arb_price), raw_sl), round_up=False)
            take_profit = align_to_tick(min(float(ara_price), raw_tp), round_up=True)

            risk = max(1.0, entry_price - stop_loss)
            reward = max(1.0, take_profit - entry_price)
            rr_ratio = round(reward / risk, 2)

            # Hitung estimasi friksi biaya transaksi
            est_fee_buy = entry_price * settings.BROKER_BUY_FEE_PCT
            est_fee_sell = take_profit * settings.BROKER_SELL_FEE_PCT
            total_fee_per_share = est_fee_buy + est_fee_sell

            clean_profit_pct = (reward - total_fee_per_share) / entry_price
            if clean_profit_pct < settings.MIN_CLEAN_PROFIT_PCT or rr_ratio < settings.MIN_RISK_REWARD_RATIO:
                signal_type = "WATCHLIST"
                rationale = f"Risk/Reward ({rr_ratio}) atau potensi profit bersih ({clean_profit_pct:.2%}) terlalu kecil setelah dipotong fee bursa."
            else:
                rationale = (
                    f"Konfirmasi Bullish: Model BiLSTM probabilitas naik {up_prob:.1%}, "
                    f"RSI di level {rsi:.1f}, harga di atas VWAP (Rp{ta['vwap']:.0f}), "
                    f"RelVol {ta['relative_volume']:.1f}x."
                )

            invalidation = f"Batal jika harga tembus breakdown di bawah VWAP (Rp{ta['vwap']:.0f}) atau menyentuh SL Rp{stop_loss}."

        elif sell_condition:
            signal_type = "SELL"
            entry_price = align_to_tick(last_price)
            stop_loss = align_to_tick(last_price + (1.5 * atr))
            take_profit = align_to_tick(last_price - (2.0 * atr))
            rr_ratio = 1.33
            total_fee_per_share = entry_price * (settings.BROKER_BUY_FEE_PCT + settings.BROKER_SELL_FEE_PCT)
            rationale = (
                f"Sinyal Exit/Take Profit: RSI ({rsi:.1f}) overbought atau breakdown tren, "
                f"BiLSTM up probabilitas rendah ({up_prob:.1%})."
            )
            invalidation = "Kembali ke posisi jika candle berikutnya breakout di atas EMA 20 dengan volume besar."

        elif watchlist_condition:
            signal_type = "WATCHLIST"
            entry_price = align_to_tick(last_price)
            stop_loss = align_to_tick(last_price - atr)
            take_profit = align_to_tick(last_price + (2 * atr))
            rr_ratio = 2.0
            total_fee_per_share = entry_price * (settings.BROKER_BUY_FEE_PCT + settings.BROKER_SELL_FEE_PCT)
            rationale = "Pergerakan volume terdeteksi; menunggu konfirmasi penembusan VWAP / pembalikan RSI."
            invalidation = "Abaikan jika harga terus sideways atau volume surut."

        else:
            signal_type = "HOLD"
            entry_price = align_to_tick(last_price)
            stop_loss = align_to_tick(last_price - atr)
            take_profit = align_to_tick(last_price + atr)
            rr_ratio = 1.0
            total_fee_per_share = entry_price * (settings.BROKER_BUY_FEE_PCT + settings.BROKER_SELL_FEE_PCT)
            rationale = "Kondisi pasar netral / sideways; tidak ada momentum yang cukup untuk scalping."
            invalidation = "Pantau hingga terjadi lonjakan volume atau crossover MACD."

        return {
            "ticker": ticker,
            "generated_at": datetime.utcnow().isoformat(),
            "timeframe": timeframe,
            "signal_type": signal_type,
            "price_at_signal": last_price,
            "lstm_predicted_return": pred_return,
            "bilstm_direction_prob": up_prob,
            "calibrated_confidence": confidence,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": rr_ratio,
            "estimated_fee_per_share": round(total_fee_per_share, 2),
            "rationale": rationale,
            "invalidation_criteria": invalidation,
            "ara_price": ara_price,
            "arb_price": arb_price
        }
