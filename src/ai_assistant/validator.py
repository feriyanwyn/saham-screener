"""Quantitative Rule-Based Validator for LLM Recommendations (Gatekeeper).
Memenuhi Ketentuan Bagian R.6:
- AI bukan penentu transaksi tunggal.
- Rule-based validation memeriksa validitas data, batas risiko, fraksi harga BEI,
  biaya transaksi, dan menolak rekomendasi jika tidak memenuhi syarat kuantitatif.
"""
from typing import Dict, Any, Tuple
from config.idx_constants import align_to_tick, get_tick_size, get_ara_arb_limits
from config.settings import settings


class AIDecisionValidator:
    """Rigorous gatekeeper validating LLM recommendations before surfacing to user."""

    @classmethod
    def validate_recommendation(
        cls, 
        ai_output: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Melakukan validasi bertingkat terhadap rekomendasi keputusan AI."""
        validated = ai_output.copy()
        decision = str(ai_output.get("decision", "NO TRADE")).upper().strip()

        # 1. Validasi Kelengkapan Data Dasar
        last_price = market_data.get("last_price", 0.0)
        if last_price <= 0:
            validated["decision"] = "NO TRADE"
            validated["validation_status"] = "REJECTED"
            validated["rejection_reason"] = "Harga pasar tidak valid atau 0."
            return validated

        # 2. Cek Saham Gocap / Papan Pemantauan Khusus Tanpa Likuiditas
        if last_price <= 50.0:
            validated["decision"] = "NO TRADE"
            validated["validation_status"] = "REJECTED"
            validated["rejection_reason"] = "Saham pada level batas bawah bursa (Rp50) tidak memenuhi kriteria scalping."
            return validated

        # Jika rekomendasi bukan BUY, loloskan sebagai status informasional
        if decision != "BUY":
            validated["validation_status"] = "APPROVED"
            validated["rejection_reason"] = None
            return validated

        # 3. Validasi Khusus Rekomendasi "BUY"
        # Ambil Stop Loss & Take Profit dari AI atau hitung fallback berdasarkan ATR
        tick = get_tick_size(last_price)
        raw_sl = float(ai_output.get("stop_loss", 0.0))
        raw_tp = float(ai_output.get("take_profit", 0.0))
        atr = float(market_data.get("atr_14", tick * 2))

        if raw_sl <= 0 or raw_sl >= last_price:
            raw_sl = last_price - (1.5 * atr)
        if raw_tp <= last_price:
            raw_tp = last_price + (2.5 * atr)

        # Selaraskan ke fraksi harga resmi BEI
        sl_aligned = align_to_tick(raw_sl, round_up=False)
        tp_aligned = align_to_tick(raw_tp, round_up=True)

        # 4. Cek Batas ARA & ARB
        prev_close = market_data.get("previous_close", last_price)
        ara_price, arb_price = get_ara_arb_limits(prev_close)

        if (ara_price - last_price) <= (2 * tick):
            validated["decision"] = "NO TRADE"
            validated["validation_status"] = "REJECTED"
            validated["rejection_reason"] = "Harga sudah mendekati batas Auto Rejection Atas (ARA < 2 tick). Risiko liquidity trap."
            return validated

        if sl_aligned < arb_price:
            sl_aligned = arb_price

        # 5. Hitung Ulang Risk / Reward Ratio Realistis
        risk = max(1.0, last_price - sl_aligned)
        reward = max(1.0, tp_aligned - last_price)
        rr_ratio = round(reward / risk, 2)

        if rr_ratio < settings.MIN_RISK_REWARD_RATIO:
            validated["decision"] = "NO TRADE"
            validated["validation_status"] = "REJECTED"
            validated["rejection_reason"] = f"Rasio Risk/Reward ({rr_ratio}x) di bawah ambang batas minimal ({settings.MIN_RISK_REWARD_RATIO}x)."
            return validated

        # 6. Validasi Friksi Biaya Transaksi (Round-trip ~0.48%)
        fee_buy = last_price * settings.BROKER_BUY_FEE_PCT
        fee_sell = tp_aligned * settings.BROKER_SELL_FEE_PCT
        net_profit_per_share = reward - (fee_buy + fee_sell)
        clean_return_pct = net_profit_per_share / last_price

        if clean_return_pct < settings.MIN_CLEAN_PROFIT_PCT:
            validated["decision"] = "NO TRADE"
            validated["validation_status"] = "REJECTED"
            validated["rejection_reason"] = f"Potensi keuntungan bersih ({clean_return_pct:.2%}) terlalu kecil setelah dipotong komisi broker dan pajak bursa."
            return validated

        # 7. Update Level yang Sudah Divalidasi dan Diselaraskan
        validated["stop_loss"] = sl_aligned
        validated["take_profit"] = tp_aligned
        validated["risk_reward_ratio"] = rr_ratio
        validated["estimated_transaction_cost"] = f"Rp {round(fee_buy + fee_sell, 2)} per share (~{(fee_buy + fee_sell)/last_price:.2%})"
        validated["validation_status"] = "APPROVED"
        validated["rejection_reason"] = None

        return validated
