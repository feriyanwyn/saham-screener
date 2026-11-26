"""Interactive AI Trading Chat Assistant grounded in live market and quant engine data."""
import json
from typing import Dict, Any, List, Optional
from src.ai_assistant.llm_provider import BaseLLMProvider, get_llm_provider
from src.ai_assistant.prompts import SYSTEM_PROMPT_CHAT


class AIChatAssistant:
    """Context-aware AI Trading Chatbot answering questions based on live system state."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    def answer_query(
        self,
        user_query: str,
        current_market_context: Optional[Dict[str, Any]] = None,
        screened_stocks: Optional[List[Dict[str, Any]]] = None,
        active_signals: Optional[List[Dict[str, Any]]] = None,
        portfolio_summary: Optional[Dict[str, Any]] = None
    ) -> str:
        """Menjawab pertanyaan pengguna dengan grounding ketat pada konteks kuantitatif terkini."""
        context_data = {
            "selected_stock_detail": current_market_context or {},
            "top_screened_stocks": (screened_stocks[:5] if screened_stocks else []),
            "recent_signals": (active_signals[:5] if active_signals else []),
            "portfolio": portfolio_summary or {}
        }

        prompt = (
            f"Konteks Data Kuantitatif & Pasar Saat Ini:\n"
            f"```json\n{json.dumps(context_data, indent=2, default=str)}\n```\n\n"
            f"Chat Question: {user_query}\n\n"
            "Instruksi Khusus:\n"
            "1. Jawab pertanyaan berdasarkan data di atas.\n"
            "2. Jika pengguna menanyakan alasan BUY/SELL/NO TRADE, jelaskan hubungan antara posisi harga terhadap VWAP, RSI, Relative Volume, dan prediksi LSTM/BiLSTM.\n"
            "3. Jika ditanyakan tentang risiko atau biaya transaksi, sebutkan angka persentase biaya resmi BEI (~0.48% round-trip) dan rasio Risk/Reward.\n"
            "4. Jangan menjanjikan keuntungan pasti. Jaga jawaban tetap ringkas, tajam, dan edukatif."
        )

        try:
            # Use real LLM if configured (non-mock), otherwise build rich quantitative response
            from src.ai_assistant.llm_provider import MockLLMProvider
            if not isinstance(self.llm, MockLLMProvider):
                return self.llm.generate_text(prompt, system_prompt=SYSTEM_PROMPT_CHAT)
        except Exception:
            pass

        return self._format_quantitative_reply(
            user_query=user_query,
            ctx=current_market_context or {},
            screened=screened_stocks or [],
            portfolio=portfolio_summary or {}
        )

    def _format_quantitative_reply(
        self,
        user_query: str,
        ctx: Dict[str, Any],
        screened: List[Dict[str, Any]],
        portfolio: Dict[str, Any]
    ) -> str:
        """Menghasilkan jawaban Copilot berbasis data kuantitatif & prediksi T+1 untuk emiten manapun."""
        quote = ctx.get("quote") or {}
        ticker = quote.get("ticker", "BBCA")
        name = quote.get("name", f"{ticker} Tbk")
        price = quote.get("last_price", 0)
        chg_pct = quote.get("change_pct", 0.0)
        rsi = ctx.get("rsi_14", quote.get("rsi_14", 50.0))
        rel_vol = ctx.get("relative_volume", quote.get("relative_volume", 1.0))
        vwap = ctx.get("vwap", price)
        sig = ctx.get("signal", quote.get("signal", "HOLD"))

        nd = ctx.get("next_day_forecast") or {}
        nd_dir = nd.get("direction", quote.get("next_day_direction", "NETRAL"))
        nd_prob = nd.get("probability", quote.get("next_day_probability", 52))
        nd_close = nd.get("target_close", price)
        nd_high = nd.get("target_high", price)
        nd_low = nd.get("target_low", price)
        nd_sl = nd.get("recommended_stop_loss", price)
        nd_rr = nd.get("risk_reward_ratio", 1.5)
        nd_action = nd.get("suggested_action", sig)

        vwap_pos = "di atas VWAP (bullish intraday)" if price >= vwap else "di bawah VWAP (tekanan jual intraday)"
        chg_str = f"+{chg_pct:.2f}%" if chg_pct >= 0 else f"{chg_pct:.2f}%"

        lines = [
            f"**Analisis Kuantitatif {ticker} ({name})**",
            f"• **Harga Terkini:** Rp {price:,.0f} ({chg_str}) | Posisi {vwap_pos} (VWAP: Rp {vwap:,.0f})",
            f"• **Indikator Teknikal:** RSI(14) = {rsi:.1f} | Relative Volume = {rel_vol:.2f}x | Sinyal Scalping: **{sig}**",
            f"• **Prediksi Hari Esok (T+1):** Arah **{nd_dir}** (Probabilitas **{nd_prob}%**) — Rekomendasi: **{nd_action}**",
            f"• **Target & Risiko:** Target Close Rp {nd_close:,.0f} | Resistance Rp {nd_high:,.0f} | Support Rp {nd_low:,.0f} | Stop Loss Rp {nd_sl:,.0f} (R/R: {nd_rr:.2f}x)",
            "• **Catatan Biaya BEI:** Perhitungkan biaya transaksi resmi ~0.48% round-trip (0.19% beli + 0.29% jual) sebelum eksekusi."
        ]

        q_lower = user_query.lower()
        if ("ranking" in q_lower or "top" in q_lower or "rekomendasi" in q_lower or "terbaik" in q_lower) and screened:
            top_items = ", ".join([
                f"{s.get('ticker')} (Skor {s.get('scalping_score', 0)}, {s.get('next_day_direction', 'NETRAL')})"
                for s in screened[:5]
            ])
            lines.append(f"• **Top Screener Saat Ini:** {top_items}")

        if portfolio and "cash" in portfolio:
            lines.append(f"• **Status Portfolio Paper:** Kas tersedia Rp {portfolio.get('cash', 0):,.0f}")

        return "\n".join(lines)
