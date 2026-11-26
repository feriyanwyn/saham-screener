"""SQLAlchemy Models representing the IDX Scalping Assistant Schema."""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, 
    DateTime, Date, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class Instrument(Base):
    """Daftar emiten terdaftar di Bursa Efek Indonesia (BEI)."""
    __tablename__ = "instruments"

    ticker = Column(String(10), primary_key=True, index=True) # e.g. BBCA, BBRI
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True, index=True)
    subsector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    board = Column(String(50), nullable=True, default="Utama", index=True) # Utama, Pengembangan, Akselerasi, Pemantauan Khusus
    shares_outstanding = Column(BigInteger, nullable=True)
    market_cap = Column(Float, nullable=True)
    listing_date = Column(Date, nullable=True)
    status = Column(String(20), default="ACTIVE", index=True) # ACTIVE, SUSPENDED, NEWLY_LISTED, DELISTED
    is_active = Column(Boolean, default=True, index=True)
    is_suspended = Column(Boolean, default=False, index=True)
    delisting_date = Column(Date, nullable=True)
    has_daily_data = Column(Boolean, default=False, index=True)
    has_intraday_data = Column(Boolean, default=False, index=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    daily_candles = relationship("DailyOHLCV", back_populates="instrument", cascade="all, delete-orphan")
    intraday_candles = relationship("IntradayOHLCV", back_populates="instrument", cascade="all, delete-orphan")
    signals = relationship("TradingSignal", back_populates="instrument")


class DailyOHLCV(Base):
    """Data historis harian OHLCV untuk analisis tren makro dan filter momentum."""
    __tablename__ = "daily_ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("instruments.ticker", ondelete="CASCADE"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    value = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=True)
    foreign_buy = Column(BigInteger, default=0)
    foreign_sell = Column(BigInteger, default=0)

    instrument = relationship("Instrument", back_populates="daily_candles")

    __table_args__ = (
        UniqueConstraint("ticker", "trade_date", name="uq_ticker_date"),
        Index("idx_daily_ticker_date", "ticker", "trade_date"),
    )


class IntradayOHLCV(Base):
    """Data candle intraday untuk scalping (1M, 5M, 15M, 1H)."""
    __tablename__ = "intraday_ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("instruments.ticker", ondelete="CASCADE"), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True) # '1M', '5M', '15M', '1H'
    candle_time = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    value = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)

    instrument = relationship("Instrument", back_populates="intraday_candles")

    __table_args__ = (
        UniqueConstraint("ticker", "timeframe", "candle_time", name="uq_intraday_candle"),
        Index("idx_intraday_lookup", "ticker", "timeframe", "candle_time"),
    )


class MLModelMeta(Base):
    """Metadata dan evaluasi performa model Machine Learning (LSTM & BiLSTM)."""
    __tablename__ = "ml_models"

    model_id = Column(String(100), primary_key=True)
    ticker = Column(String(10), nullable=True) # Null jika model global
    architecture = Column(String(20), nullable=False) # 'LSTM', 'BiLSTM'
    timeframe = Column(String(5), nullable=False)
    features_used = Column(Text, nullable=False) # JSON list
    training_start_date = Column(Date, nullable=False)
    training_end_date = Column(Date, nullable=False)
    test_mae = Column(Float, nullable=True)
    test_rmse = Column(Float, nullable=True)
    test_directional_accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    weights_path = Column(String(255), nullable=False)
    scaler_path = Column(String(255), nullable=False)
    version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TradingSignal(Base):
    """Log sinyal scalping yang dihasilkan oleh signal engine."""
    __tablename__ = "trading_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("instruments.ticker"), nullable=False, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    timeframe = Column(String(5), nullable=False)
    signal_type = Column(String(10), nullable=False, index=True) # 'BUY', 'SELL', 'HOLD', 'WATCHLIST'
    price_at_signal = Column(Float, nullable=False)
    lstm_predicted_return = Column(Float, nullable=True)
    bilstm_direction_prob = Column(Float, nullable=True)
    calibrated_confidence = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)
    estimated_fee = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    invalidation_criteria = Column(Text, nullable=False)
    status = Column(String(20), default="ACTIVE", index=True) # 'ACTIVE', 'EXECUTED', 'CANCELLED', 'EXPIRED'

    instrument = relationship("Instrument", back_populates="signals")


class PaperAccount(Base):
    """Akun paper trading simulasi saldo virtual."""
    __tablename__ = "paper_accounts"

    account_id = Column(String(50), primary_key=True)
    initial_balance = Column(Float, nullable=False, default=10000000.0) # Rp 10 Juta
    current_cash = Column(Float, nullable=False, default=10000000.0)
    total_equity = Column(Float, nullable=False, default=10000000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    positions = relationship("PaperPosition", back_populates="account")
    orders = relationship("PaperOrder", back_populates="account")


class PaperPosition(Base):
    """Posisi terbuka pada akun paper trading."""
    __tablename__ = "paper_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), ForeignKey("paper_accounts.account_id"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    lot_quantity = Column(Integer, nullable=False)
    average_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("PaperAccount", back_populates="positions")


class PaperOrder(Base):
    """Histori transaksi eksekusi paper trading."""
    __tablename__ = "paper_orders"

    order_id = Column(String(100), primary_key=True)
    account_id = Column(String(50), ForeignKey("paper_accounts.account_id"), nullable=False, index=True)
    signal_id = Column(BigInteger, ForeignKey("trading_signals.id"), nullable=True)
    ticker = Column(String(10), nullable=False, index=True)
    order_type = Column(String(10), nullable=False) # 'BUY', 'SELL'
    order_price = Column(Float, nullable=False)
    lot_quantity = Column(Integer, nullable=False)
    gross_amount = Column(Float, nullable=False)
    fee_broker = Column(Float, nullable=False)
    fee_levy = Column(Float, nullable=False)
    tax_pph = Column(Float, nullable=False)
    tax_ppn = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    slippage_realized = Column(Float, default=0.0)
    execution_status = Column(String(20), nullable=False) # 'FILLED', 'REJECTED'
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)

    account = relationship("PaperAccount", back_populates="orders")


class BacktestRun(Base):
    """Catatan riwayat backtesting strategi kuantitatif."""
    __tablename__ = "backtest_runs"

    run_id = Column(String(100), primary_key=True)
    strategy_name = Column(String(100), nullable=False)
    tickers = Column(Text, nullable=False) # JSON array of tickers
    timeframe = Column(String(5), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    gross_profit = Column(Float, nullable=False)
    gross_loss = Column(Float, nullable=False)
    net_profit = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    expectancy = Column(Float, nullable=True)
    parameters = Column(Text, nullable=False) # JSON dictionary
    equity_curve = Column(Text, nullable=False) # JSON array of {date, equity}
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketScanResult(Base):
    """Hasil pemindaian pasar menyeluruh (Full Market Scan & Sector Scan)."""
    __tablename__ = "market_scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True, index=True)
    last_price = Column(Float, nullable=False)
    change_pct = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    value = Column(Float, nullable=False)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    is_above_vwap = Column(Boolean, default=False)
    lstm_predicted_return = Column(Float, nullable=True)
    bilstm_direction_prob = Column(Float, nullable=True)
    signal_type = Column(String(20), nullable=False, index=True) # BUY, SELL, HOLD, WATCHLIST
    technical_score = Column(Float, default=0.0)
    ai_confidence = Column(Float, default=0.5)
    opportunity_rank = Column(Integer, default=0)
    ranking_category = Column(String(50), nullable=True, index=True) # TOP_BULLISH, TOP_BEARISH, HIGHEST_VOLUME, STRONGEST_MOMENTUM, LOWEST_RISK, POTENTIAL_SCALPING
    has_sufficient_data = Column(Boolean, default=True)
    scanned_at = Column(DateTime, default=datetime.utcnow, index=True)
