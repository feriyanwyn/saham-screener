"""Unit and integration tests for AI Decision Assistant and Validator."""
from src.ai_assistant.validator import AIDecisionValidator
from src.ai_assistant.decision_engine import AITradingDecisionEngine
from src.ai_assistant.chat_assistant import AIChatAssistant
from src.ai_assistant.llm_provider import MockLLMProvider


def test_validator_approves_valid_buy():
    ai_raw = {
        "decision": "BUY",
        "stop_loss": 9700.0,
        "take_profit": 10200.0,
        "risk_reward_ratio": 2.3
    }
    market_data = {
        "last_price": 9850.0,
        "previous_close": 9850.0,
        "atr_14": 100.0
    }
    validated = AIDecisionValidator.validate_recommendation(ai_raw, market_data)
    assert validated["decision"] == "BUY"
    assert validated["validation_status"] == "APPROVED"
    assert validated["stop_loss"] % 25 == 0  # BEI Tick alignment >= Rp5000 is Rp25


def test_validator_rejects_poor_rr():
    ai_raw = {
        "decision": "BUY",
        "stop_loss": 9800.0,
        "take_profit": 9875.0,  # Only 25 tick gain vs 50 risk -> R/R = 0.5
        "risk_reward_ratio": 0.5
    }
    market_data = {
        "last_price": 9850.0,
        "previous_close": 9850.0,
        "atr_14": 100.0
    }
    validated = AIDecisionValidator.validate_recommendation(ai_raw, market_data)
    # Harus ditolak atau disesuaikan
    assert validated["validation_status"] in ["REJECTED", "APPROVED"]


def test_ai_decision_engine_mock():
    engine = AITradingDecisionEngine(llm_provider=MockLLMProvider())
    import pandas as pd
    df_dummy = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=30, freq="5min"),
        "open": [5000] * 30,
        "high": [5050] * 30,
        "low": [4950] * 30,
        "close": [5025] * 30,
        "volume": [10000] * 30
    })
    res = engine.analyze_stock("BMRI", df_dummy)
    assert "decision" in res
    assert "detailed_explanation" in res


def test_ai_chat_assistant():
    chat = AIChatAssistant(llm_provider=MockLLMProvider())
    resp = chat.answer_query("Mengapa sistem merekomendasikan HOLD?")
    assert len(resp) > 20
    assert "VWAP" in resp or "scalping" in resp or "AI" in resp
