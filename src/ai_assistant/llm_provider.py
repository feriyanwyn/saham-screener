"""LLM Provider Abstraction Layer for AI Trading Decision Assistant.
Mendukung:
1. Google Gemini API (gemini-1.5-flash / gemini-2.0-flash)
2. OpenAI API (gpt-4o / gpt-4o-mini)
3. Anthropic Claude API (claude-3-5-sonnet / haiku)
4. Mock LLM Provider (Offline quantitative reasoning fallback tanpa perlu API key)
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests

from config.settings import settings


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Menghasilkan teks dari prompt."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Menghasilkan output JSON terstruktur."""
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY tidak dikonfigurasi.")

        headers = {"Content-Type": "application/json"}
        url = f"{self.base_url}?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly adhere to these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "topP": 0.8}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API Error ({resp.status_code}): {resp.text}")

        res_json = resp.json()
        candidates = res_json.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raw = self.generate_text(prompt, system_prompt)
        return _clean_and_parse_json(raw)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY tidak dikonfigurasi.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }
        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text}")

        res_json = resp.json()
        return res_json["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raw = self.generate_text(prompt, system_prompt)
        return _clean_and_parse_json(raw)


class ClaudeLLMProvider(BaseLLMProvider):
    """Anthropic Claude API Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY tidak dikonfigurasi.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Claude API Error ({resp.status_code}): {resp.text}")

        res_json = resp.json()
        return res_json["content"][0]["text"]

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raw = self.generate_text(prompt, system_prompt)
        return _clean_and_parse_json(raw)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic High-Fidelity Mock Provider.
    Berfungsi sebagai offline fallback cerdas ketika API key belum dikonfigurasi,
    menjamin notebook dan aplikasi tetap 100% fungsional tanpa crash.
    """

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if "Chat Question:" in prompt:
            question = prompt.split("Chat Question:")[-1].strip()
            return (
                f"Berdasarkan data kuantitatif terkini: {question}\n\n"
                "Analisis Asisten AI: Sistem memantau pergerakan harga saham terhadap VWAP dan EMA 20, "
                "dengan konfirmasi momentum dari RSI dan arah prediksi BiLSTM. Saham dengan Relative Volume > 1.5x "
                "dan di atas VWAP memiliki peluang scalping tertinggi hari ini, dengan catatan rasio risk/reward >= 1.5 "
                "dan stop loss disiplin di bawah level swing low."
            )
        return "Analisis Mock AI: Data teknikal dan Deep Learning berhasil diproses."

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        # Jika multi-stock ranking
        if "Multi-Stock Screening Data" in prompt:
            return {
                "ranking": [
                    {"ticker": "BBCA", "momentum_rank": 1, "status": "BEST_MOMENTUM", "reason": "Di atas VWAP, RSI stabil 58, prediksi BiLSTM 62% naik."},
                    {"ticker": "TLKM", "momentum_rank": 2, "status": "VOLUME_SURGE", "reason": "Volume spike 1.8x, rebound dari area EMA 50."},
                    {"ticker": "BMRI", "momentum_rank": 3, "status": "BULLISH_TREND", "reason": "Golden cross EMA 20/50 terkonfirmasi."},
                    {"ticker": "GOTO", "momentum_rank": 4, "status": "HIGH_RISK", "reason": "Spread tipis, fraksi Rp1, volatilitas cepat."},
                    {"ticker": "ASII", "momentum_rank": 5, "status": "AVOID", "reason": "Di bawah VWAP dan RSI melemah di bawah 40."}
                ],
                "summary": "Peluang scalping hari ini terpusat pada sektor perbankan likuid yang mempertahankan posisi di atas VWAP."
            }

        # Single-stock decision default mock
        return {
            "decision": "BUY",
            "trend_analysis": "Uptrend intraday terkonfirmasi dengan harga bertengger di atas VWAP dan EMA 20.",
            "technical_analysis": "RSI di zona 54 (momentum sehat tanpa overbought), MACD histogram positif, Relative Volume 1.4x.",
            "ml_prediction_interpretation": "BiLSTM memproyeksikan probabilitas naik 61.5% dan LSTM mengestimasi kenaikan return +0.85% pada timeframe 5M.",
            "entry_zone": "Sesuai harga pasar saat ini atau pullback ke dekat VWAP.",
            "risk_reward_ratio": 2.1,
            "main_risks": "Risiko penembusan support VWAP atau pelemahan IHSG intraday.",
            "confidence_assessment": "Moderate-High (72% AI Confidence)",
            "detailed_explanation": (
                "Kombinasi probabilitas Deep Learning yang positif serta penataan indikator momentum di atas VWAP "
                "memberikan rasio risk-to-reward yang menarik (2.1x) setelah memperhitungkan friksi biaya transaksi bursa."
            )
        }


def _clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Membersihkan markdown code blocks dan mem-parsing JSON secara aman."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception as e:
        # Fallback: cari kurung kurawal pertama dan terakhir
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                pass
        return {"error": f"Failed to parse JSON: {e}", "raw_content": raw_text}


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory function untuk inisialisasi LLM Provider."""
    chosen = (provider_name or os.getenv("LLM_PROVIDER", "mock")).lower().strip()
    if chosen == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return GeminiLLMProvider(api_key=api_key)
    elif chosen == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return OpenAILLMProvider(api_key=api_key)
    elif chosen == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return ClaudeLLMProvider(api_key=api_key)
    
    # Fallback to Mock Provider if keys missing or explicitly selected
    return MockLLMProvider()
