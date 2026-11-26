"""Application Settings & Environment Loader without external pydantic_settings dependency."""
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    APP_NAME: str = "AI-Powered Indonesian Stock Prediction & Scalping Assistant"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'data' / 'idx_scalper.db'}"
    )
    
    # Provider Settings
    DEFAULT_DATA_PROVIDER: str = os.getenv("DEFAULT_DATA_PROVIDER", "yfinance")
    INVEZGO_API_KEY: str = os.getenv("INVEZGO_API_KEY", "")
    INVEZGO_BASE_URL: str = os.getenv("INVEZGO_BASE_URL", "https://api.invezgo.com")
    APICOID_API_KEY: str = os.getenv("APICOID_API_KEY", "")
    APICOID_BASE_URL: str = os.getenv("APICOID_BASE_URL", "https://use.api.co.id")
    
    # Risk & Sizing Parameters
    INITIAL_CAPITAL_IDR: float = float(os.getenv("INITIAL_CAPITAL_IDR", "10000000.00"))
    MAX_RISK_PER_TRADE_PCT: float = float(os.getenv("MAX_RISK_PER_TRADE_PCT", "0.015"))
    MAX_DAILY_LOSS_PCT: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.03"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
    BROKER_BUY_FEE_PCT: float = float(os.getenv("BROKER_BUY_FEE_PCT", "0.0019"))
    BROKER_SELL_FEE_PCT: float = float(os.getenv("BROKER_SELL_FEE_PCT", "0.0029"))
    MIN_RISK_REWARD_RATIO: float = float(os.getenv("MIN_RISK_REWARD_RATIO", "1.5"))
    MIN_CLEAN_PROFIT_PCT: float = float(os.getenv("MIN_CLEAN_PROFIT_PCT", "0.012"))


# Global Settings Instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR / "raw", exist_ok=True)
os.makedirs(settings.DATA_DIR / "processed", exist_ok=True)
os.makedirs(settings.MODELS_DIR / "lstm", exist_ok=True)
os.makedirs(settings.MODELS_DIR / "bilstm", exist_ok=True)
