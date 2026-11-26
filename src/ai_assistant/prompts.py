"""Structured Prompts and System Instructions for AI Trading Decision Assistant.
Menjamin bahwa LLM bertindak sebagai Senior Quantitative Trader & Risk Analyst,
tidak mengarang data, dan mengembalikan format JSON yang konsisten.
"""
import json
from typing import Dict, Any, List


SYSTEM_PROMPT_ANALYST = """Anda adalah Senior AI Quantitative Analyst & Professional Scalping Assistant untuk Bursa Efek Indonesia (BEI/IDX).
Tugas Anda adalah menginterpretasikan data teknikal, model Machine Learning (LSTM & BiLSTM), likuiditas, dan manajemen risiko untuk menghasilkan analisis trading scalping yang objektif dan terukur.

ATURAN WAJIB:
1. JANGAN PERNAH MENGARANG DATA ATAU ANGKA. Gunakan hanya angka dan fitur yang diberikan dalam prompt.
2. Keputusan yang diperbolehkan hanya: "BUY", "SELL", "HOLD", atau "NO TRADE".
3. Jangan pernah menjamin profit atau kepastian arah pasar.
4. Setiap keputusan "BUY" WAJIB memiliki rasio Risk/Reward minimal 1.5, memperhitungkan friksi biaya transaksi bursa (~0.48% round-trip), dan stop loss yang realistis di bawah level support/VWAP/ATR.
5. Jika data teknikal bertentangan dengan prediksi ML, atau pasar sideways tanpa likuiditas, pilih "HOLD" atau "NO TRADE".
6. Format output HARUS berupa JSON valid tanpa teks pengantar atau penutup di luar JSON.
"""

SYSTEM_PROMPT_CHAT = """Anda adalah Asisten Interaktif AI untuk Trading Saham Indonesia (BEI/IDX).
Anda membantu pengguna menjawab pertanyaan tentang scalping, indikator teknikal (RSI, MACD, VWAP, EMA), prediksi model LSTM & BiLSTM, serta manajemen risiko.
Jawab secara ringkas, profesional, berpatokan ketat pada data kuantitatif yang tersedia, dan jangan memberikan janji profit pasti.
"""


def build_single_stock_analysis_prompt(data: Dict[str, Any]) -> str:
    """Membangun prompt analisis komprehensif saham tunggal untuk LLM."""
    payload = {
        "stock_ticker": data.get("ticker"),
        "last_price": data.get("last_price"),
        "open_price": data.get("open"),
        "high_price": data.get("high"),
        "low_price": data.get("low"),
        "previous_close": data.get("previous_close"),
        "price_change_pct": data.get("change_pct"),
        "volume": data.get("volume"),
        "transaction_value_idr": data.get("value"),
        "relative_volume_20": data.get("relative_volume"),
        "bid_ask_spread_ticks": data.get("spread_ticks"),
        "best_bid": data.get("best_bid"),
        "best_ask": data.get("best_ask"),
        "technical_indicators": {
            "rsi_14": data.get("rsi_14"),
            "macd": data.get("macd"),
            "macd_signal": data.get("macd_signal"),
            "macd_hist": data.get("macd_hist"),
            "is_macd_bullish": data.get("is_macd_bullish"),
            "ema_9": data.get("ema_9"),
            "ema_20": data.get("ema_20"),
            "ema_50": data.get("ema_50"),
            "vwap": data.get("vwap"),
            "is_above_vwap": data.get("is_above_vwap"),
            "atr_14": data.get("atr_14")
        },
        "deep_learning_predictions": {
            "lstm_expected_return": data.get("lstm_predicted_return"),
            "bilstm_up_probability": data.get("bilstm_direction_prob"),
            "calibrated_ai_confidence": data.get("calibrated_confidence")
        },
        "market_and_fees": {
            "market_index_ihsg": data.get("ihsg_status", "NEUTRAL"),
            "estimated_roundtrip_fee_pct": 0.48,
            "ara_limit": data.get("ara_price"),
            "arb_limit": data.get("arb_price")
        }
    }

    schema_example = {
        "stock_ticker": data.get("ticker"),
        "analysis_timestamp": data.get("timestamp"),
        "decision": "BUY | SELL | HOLD | NO TRADE",
        "trend_analysis": "Penjelasan tren harga jangka pendek dan posisi terhadap EMA/VWAP.",
        "technical_analysis": "Penjelasan momentum RSI, crossover MACD, dan aktivitas volume.",
        "ml_prediction_interpretation": "Interpretasi return LSTM dan probabilitas BiLSTM.",
        "entry_zone": "Rentang harga entry yang direkomendasikan.",
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "risk_reward_ratio": 0.0,
        "estimated_transaction_cost": "Estimasi biaya bursa dalam nominal atau persentase.",
        "main_risks": "Identifikasi risiko utama (misal false breakout, gap down, likuiditas).",
        "confidence_assessment": "Tingkat keyakinan analisis (High / Medium / Low) dan alasannya.",
        "detailed_explanation": "Penjelasan komprehensif logis di balik rekomendasi keputusan.",
        "invalidation_criteria": "Kondisi pasti yang membatalkan rekomendasi ini."
    }

    return (
        f"Berikut adalah data pasar kuantitatif terkini untuk saham {data.get('ticker')}:\n\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"Lakukan analisis mendalam dan kembalikan output persis dalam format JSON dengan skema berikut:\n\n"
        f"```json\n{json.dumps(schema_example, indent=2)}\n```"
    )


def build_multi_stock_ranking_prompt(stocks_data: List[Dict[str, Any]]) -> str:
    """Membangun prompt analisis multi-saham hasil screening untuk pemeringkatan kualitas peluang."""
    simplified_list = []
    for s in stocks_data:
        simplified_list.append({
            "ticker": s.get("ticker"),
            "last_price": s.get("last_price"),
            "change_pct": s.get("change_pct"),
            "opportunity_score": s.get("opportunity_score"),
            "relative_volume": s.get("relative_volume"),
            "rsi_14": s.get("rsi_14"),
            "is_above_vwap": s.get("is_above_vwap"),
            "spread_ticks": s.get("spread_ticks"),
            "value_idr": s.get("value")
        })

    schema_example = {
        "ranking": [
            {
                "ticker": "KODE",
                "momentum_rank": 1,
                "category": "BEST_MOMENTUM | VOLUME_SURGE | BULLISH_TREND | HIGH_RISK | AVOID",
                "recommended_action": "BUY | WATCHLIST | AVOID",
                "reason": "Alasan singkat mengapa saham ini ditempatkan pada ranking tersebut."
            }
        ],
        "top_pick": "KODE saham terbaik hari ini jika ada yang memenuhi kriteria, atau null jika tidak ada yang layak.",
        "market_summary": "Ringkasan ikhtisar kondisi pasar hasil pemindaian saham."
    }

    return (
        "Berikut adalah Multi-Stock Screening Data dari Bursa Efek Indonesia (BEI):\n\n"
        f"```json\n{json.dumps(simplified_list, indent=2, default=str)}\n```\n\n"
        "Urutkan saham-saham di atas berdasarkan kualitas peluang scalping, identifikasi saham dengan momentum terbaik, "
        "lonjakan volume, tren bullish, risiko tinggi, dan saham yang harus dihindari. Jangan memaksakan sinyal BUY "
        "jika tidak ada yang memenuhi syarat.\n\n"
        f"Kembalikan format JSON persis seperti ini:\n```json\n{json.dumps(schema_example, indent=2)}\n```"
    )
