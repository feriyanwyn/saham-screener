"""FastAPI REST Service for AI-Powered IDX Stock Prediction & Scalping Assistant."""
from typing import Optional, List, Dict, Any
import os
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pandas as pd
import yfinance as yf

from config.settings import settings
from config.idx_constants import IDX_SECTORS, IDX_BOARDS, IDX_STATUSES, align_to_tick, get_tick_size
from database.connection import get_db, init_db
from src.data_collection import get_data_provider, UniverseManager
from src.data_collection.idx_master_data import seed_idx_master_database, get_idx_coverage_stats, IDX_MASTER_SEED
from src.stock_screener import StockScreener, FullMarketScanner
from src.signal_engine.engine import ScalpingSignalEngine
from src.paper_trading.account import PaperTradingSimulator
from src.technical_analysis.indicators import TechnicalAnalysisEngine
from src.machine_learning.trainer import ModelPipeline
from src.machine_learning.next_day_predictor import next_day_predictor
from src.ai_assistant.decision_engine import AITradingDecisionEngine
from src.ai_assistant.chat_assistant import AIChatAssistant
from src.backtesting.engine import BacktestEngine

app = FastAPI(
    title=settings.APP_NAME,
    description="REST API backend for IDX stock analysis, screener, ML prediction, and paper trading.",
    version="1.0.0"
)

# Enable CORS for Next.js, Streamlit, and mobile web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure yfinance cache in /tmp for serverless environments (Vercel)
if os.getenv("VERCEL"):
    try:
        os.makedirs("/tmp/py-yfinance", exist_ok=True)
        yf.set_tz_cache_location("/tmp/py-yfinance")
    except Exception:
        pass

# Inisialisasi DB saat startup
try:
    init_db()
except Exception:
    pass


class BuyOrderRequest(BaseModel):
    ticker: str
    price: float
    lots: int
    stop_loss: float
    take_profit: float


class SellOrderRequest(BaseModel):
    ticker: str
    price: float
    lots: Optional[int] = None


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/api/instruments")
def get_instruments(provider_name: Optional[str] = None):
    provider = get_data_provider(provider_name)
    return {"instruments": provider.get_instruments()}


@app.get("/api/quote/{ticker}")
def get_quote(ticker: str, provider_name: Optional[str] = None):
    provider = get_data_provider(provider_name)
    quote = provider.get_live_quote(ticker)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for ticker {ticker}")
    return quote


@app.get("/api/screener")
def run_screener(
    min_value: float = Query(100_000_000.0, description="Min transaction value in IDR"),
    min_rel_vol: float = Query(1.0, description="Min Relative Volume"),
    max_spread: int = Query(3, description="Max spread ticks"),
    provider_name: Optional[str] = None
):
    provider = get_data_provider(provider_name)
    screener = StockScreener(provider)
    results = screener.screen_stocks(
        min_value_idr=min_value,
        min_rel_volume=min_rel_vol,
        max_spread_ticks=max_spread
    )
    return {"count": len(results), "results": results}


@app.get("/api/signal/{ticker}")
def get_signal(ticker: str, timeframe: str = "5M", provider_name: Optional[str] = None):
    provider = get_data_provider(provider_name)
    df = provider.get_intraday_data(ticker, timeframe=timeframe.lower(), limit=80)
    if df.empty or len(df) < 20:
        raise HTTPException(status_code=400, detail="Insufficient intraday candles for signal generation")
    
    engine = ScalpingSignalEngine()
    signal = engine.generate_signal(df, ticker=ticker, timeframe=timeframe)
    return signal


@app.get("/api/portfolio")
def get_portfolio(account_id: str = "MAIN_PAPER_ACCOUNT", db: Session = Depends(get_db)):
    sim = PaperTradingSimulator(account_id=account_id, db_session=db)
    return sim.get_portfolio_summary()


@app.post("/api/paper/buy")
def execute_paper_buy(req: BuyOrderRequest, account_id: str = "MAIN_PAPER_ACCOUNT", db: Session = Depends(get_db)):
    sim = PaperTradingSimulator(account_id=account_id, db_session=db)
    res = sim.execute_buy(
        ticker=req.ticker,
        price=req.price,
        lots=req.lots,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit
    )
    if res["status"] != "FILLED":
        raise HTTPException(status_code=400, detail=res["reason"])
    return res


# =====================================================================
# Market Explorer & Full IDX Database Endpoints (Bagian A, B, C, D)
# =====================================================================

@app.get("/api/market/sectors")
def get_idx_sectors():
    """Mengembalikan daftar 12 sektor IDX-IC resmi beserta nama ID dan EN."""
    return {"sectors": IDX_SECTORS}


@app.get("/api/market/coverage-stats")
def get_market_coverage_stats(db: Session = Depends(get_db)):
    """Mengembalikan metrik cakupan database seluruh emiten BEI dan kemampuan provider."""
    return get_idx_coverage_stats(db)


@app.get("/api/market/explorer")
def explore_stocks(
    search: Optional[str] = Query(None, description="Pencarian kode ticker atau nama perusahaan"),
    sector: Optional[str] = Query(None, description="Filter sektor IDX-IC"),
    board: Optional[str] = Query(None, description="Filter papan: Utama, Pengembangan, Akselerasi, Pemantauan Khusus"),
    status: Optional[str] = Query("ALL", description="Filter status: ALL, ACTIVE, SUSPENDED, NEWLY_LISTED, DELISTED"),
    sort_by: str = Query("ticker", description="Kolom sorting: ticker, name, sector, board, listing_date"),
    sort_order: str = Query("asc", description="asc atau desc"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    page_size: int = Query(25, ge=5, le=100, description="Jumlah baris per halaman (25, 50, 100)"),
    db: Session = Depends(get_db)
):
    """Pencarian dan pemfilteran seluruh emiten BEI dengan backend pagination."""
    mgr = UniverseManager(db_session=db)
    # Pastikan master terisi
    stats = mgr.get_coverage_statistics()
    if stats["total_listed_idx"] == 0:
        mgr.sync_instruments()

    res = mgr.get_explorer_stocks(
        search=search,
        sector=sector,
        board=board,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    return res


@app.post("/api/market/sync")
def trigger_master_sync(force_refresh: bool = False, db: Session = Depends(get_db)):
    """Memperbarui master database emiten BEI."""
    mgr = UniverseManager(db_session=db)
    count = mgr.sync_instruments(force_seed=force_refresh)
    return {"status": "ok", "synced_emiten_count": count, "timestamp": get_idx_coverage_stats(db)["last_synced_at"]}


class ScanMarketRequest(BaseModel):
    sector_filter: Optional[str] = "ALL"
    max_stocks: Optional[int] = 50
    timeframe: Optional[str] = "5m"


@app.post("/api/market/scan")
def trigger_market_scan(
    req: ScanMarketRequest,
    provider_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Menjalankan full market scan atau scan sektoral dan menyimpan hasil ke database."""
    provider = get_data_provider(provider_name)
    scanner = FullMarketScanner(provider=provider, db_session=db)
    res = scanner.run_scan(
        sector_filter=req.sector_filter,
        max_stocks=req.max_stocks,
        timeframe=req.timeframe or "5m"
    )
    return res


@app.get("/api/market/scan-results")
def get_cached_scan_results(
    category: Optional[str] = Query(None, description="Kategori: TOP_BULLISH, TOP_BEARISH, HIGHEST_VOLUME, STRONGEST_MOMENTUM, LOWEST_RISK, POTENTIAL_SCALPING"),
    sector: Optional[str] = Query(None, description="Filter sektor"),
    signal_type: Optional[str] = Query(None, description="BUY, SELL, HOLD, WATCHLIST"),
    limit: int = Query(50, ge=5, le=100),
    provider_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mengambil hasil ranking scan terbaru dari database cache tanpa hitung ulang."""
    provider = get_data_provider(provider_name)
    scanner = FullMarketScanner(provider=provider, db_session=db)
    results = scanner.get_latest_cached_scan(
        category=category,
        sector=sector,
        signal_type=signal_type,
        limit=limit
    )
    return {"count": len(results), "results": results}


# =====================================================================
# Real Market Data Cache & Yahoo Finance Helper
# =====================================================================

_OVERVIEW_CACHE: Dict[str, Any] = {}
_OVERVIEW_TIMESTAMP: float = 0.0
_REAL_SCREENER_CACHE: List[Dict[str, Any]] = []
_REAL_SCREENER_TIMESTAMP: float = 0.0
_LIVE_QUOTES_CACHE: Dict[str, Dict[str, Any]] = {}


def _synthesize_emiten_quote(item: Dict[str, Any]) -> Dict[str, Any]:
    """Menghasilkan quote realistis untuk emiten yang belum ada feed live real-time."""
    ticker = item["ticker"]
    seed_val = sum(ord(c) * (i + 1) for i, c in enumerate(ticker))

    sector = item.get("sector", "General")
    if sector == "Financials":
        base_prices = [1120, 1840, 2100, 2350, 2980, 3070, 3570, 3980, 5800]
    elif sector == "Energy":
        base_prices = [460, 1150, 1220, 1380, 1480, 1520, 1750, 2650, 3680, 6800]
    elif sector == "Basic Materials":
        base_prices = [510, 890, 980, 1450, 2250, 3450, 3780, 6800, 7200, 8950]
    elif sector == "Technology":
        base_prices = [54, 118, 220, 440, 450, 890]
    elif sector == "Consumer Non-Cyclicals":
        base_prices = [420, 680, 1420, 1850, 2550, 3150, 4950, 5150, 6850, 11800]
    elif sector == "Infrastructures":
        base_prices = [780, 1890, 2040, 2150, 2180, 4650]
    else:
        base_prices = [320, 430, 540, 750, 820, 1050, 1180, 1320, 1450, 1850, 2150, 2750, 4650]

    base_price = base_prices[seed_val % len(base_prices)]
    last_price = align_to_tick(base_price)

    raw_pct = ((seed_val % 91) - 45) / 10.0
    change_pct = round(raw_pct, 2)
    change = round(last_price * (change_pct / 100.0), 2)
    prev_close = last_price - change

    rel_vol = round(0.75 + (seed_val % 22) / 10.0, 2)
    vol_shares = int((seed_val % 50 + 5) * 100_000 * rel_vol)
    rsi_est = round(min(85.0, max(25.0, 50.0 + (change_pct * 3.2))), 1)

    if change_pct >= 1.2 and rel_vol >= 1.0:
        signal = "BUY"
        score = min(96, int(70 + change_pct * 3 + rel_vol * 4))
    elif change_pct <= -1.5:
        signal = "SELL"
        score = max(20, int(42 + change_pct * 4))
    else:
        signal = "HOLD"
        score = max(35, int(48 + change_pct * 2))

    # Next-Day (T+1) Prediction
    if change_pct >= 0.8 or (score >= 65 and rel_vol >= 1.05):
        next_day_dir = "NAIK"
        next_day_prob = min(88, int(60 + change_pct * 3 + (score - 60) * 0.4))
    elif change_pct <= -1.0 or score <= 40:
        next_day_dir = "TURUN"
        next_day_prob = min(85, int(60 + abs(change_pct) * 3 + (50 - score) * 0.5))
    else:
        next_day_dir = "NETRAL"
        next_day_prob = 52

    return {
        "ticker": ticker,
        "name": item.get("name", f"{ticker} Tbk"),
        "sector": item.get("sector", "General"),
        "board": item.get("board", "Utama"),
        "last_price": last_price,
        "open": last_price - round(change * 0.4),
        "high": max(last_price, last_price + abs(change)),
        "low": min(last_price, last_price - abs(change)),
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "volume": vol_shares,
        "value": vol_shares * last_price,
        "relative_volume": rel_vol,
        "rsi_14": rsi_est,
        "signal": signal,
        "scalping_score": score,
        "next_day_direction": next_day_dir,
        "next_day_probability": next_day_prob,
        "status": item.get("status", "ACTIVE"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }


def _build_quote_payload(
    ticker: str,
    item: Dict[str, Any],
    last_price: float,
    prev_close: float,
    day_open: float,
    day_high: float,
    day_low: float,
    volume: int,
    data_source: str,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    rel_vol: Optional[float] = None,
    rsi_est: Optional[float] = None,
) -> Dict[str, Any]:
    change = round(last_price - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
    rel_vol_val = rel_vol if rel_vol is not None else round(max(0.1, min(5.0, (volume / 12_000_000) if volume > 0 else 1.0)), 2)
    rsi_val = rsi_est if rsi_est is not None else round(min(88.0, max(22.0, 50.0 + (change_pct * 3.2))), 1)

    if change_pct >= 1.5 and rel_vol_val >= 1.1:
        signal = "BUY"
        score = min(96, int(72 + change_pct * 3 + rel_vol_val * 4))
    elif change_pct <= -1.8:
        signal = "SELL"
        score = max(20, int(42 + change_pct * 4))
    elif change_pct > 0:
        signal = "BUY" if rel_vol_val >= 1.3 else "HOLD"
        score = min(90, int(58 + change_pct * 2 + rel_vol_val * 3))
    else:
        signal = "HOLD"
        score = max(35, int(48 + change_pct * 2))

    if change_pct >= 0.8 or (score >= 65 and rel_vol_val >= 1.05):
        next_day_dir = "NAIK"
        next_day_prob = min(88, int(60 + change_pct * 3 + (score - 60) * 0.4))
    elif change_pct <= -1.0 or score <= 40:
        next_day_dir = "TURUN"
        next_day_prob = min(85, int(60 + abs(change_pct) * 3 + (50 - score) * 0.5))
    else:
        next_day_dir = "NETRAL"
        next_day_prob = 52

    aligned_last = align_to_tick(last_price)
    orderbook_available = bool(bid and ask and bid > 0 and ask > 0)
    spread_ticks = None
    if orderbook_available:
        tick = get_tick_size(aligned_last)
        spread_ticks = max(1, round((ask - bid) / tick)) if tick > 0 else 1

    return {
        "ticker": ticker,
        "name": item.get("name", f"{ticker} Tbk"),
        "sector": item.get("sector", "General"),
        "board": item.get("board", "Utama"),
        "last_price": aligned_last,
        "open": align_to_tick(day_open) if day_open > 0 else aligned_last,
        "high": align_to_tick(day_high) if day_high > 0 else aligned_last,
        "low": align_to_tick(day_low) if day_low > 0 else aligned_last,
        "previous_close": align_to_tick(prev_close) if prev_close > 0 else aligned_last,
        "change": change,
        "change_pct": change_pct,
        "volume": volume,
        "value": volume * aligned_last,
        "bid": align_to_tick(bid) if orderbook_available else None,
        "ask": align_to_tick(ask) if orderbook_available else None,
        "spread_ticks": spread_ticks,
        "orderbook_available": orderbook_available,
        "relative_volume": rel_vol_val,
        "rsi_14": rsi_val,
        "signal": signal,
        "scalping_score": score,
        "next_day_direction": next_day_dir,
        "next_day_probability": next_day_prob,
        "status": item.get("status", "ACTIVE"),
        "data_source": data_source,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _fetch_single_real_quote(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch real-time quote using priority: 1) Invezgo, 2) Api.co.id, 3) Yahoo Finance."""
    ticker = item["ticker"]

    # 1. Invezgo API (if API key configured)
    if settings.INVEZGO_API_KEY:
        try:
            from src.data_collection.invezgo_provider import InvezgoProvider
            inv = InvezgoProvider()
            q = inv.get_live_quote(ticker)
            if q and q.get("last_price") or (q and q.get("close")):
                lp = float(q.get("last_price") or q.get("close"))
                pc = float(q.get("previous_close") or lp)
                ob = inv.get_order_book(ticker)
                top_bid = float(ob["bids"][0]["price"]) if ob.get("bids") else None
                top_ask = float(ob["asks"][0]["price"]) if ob.get("asks") else None
                payload = _build_quote_payload(
                    ticker, item, lp, pc,
                    float(q.get("open") or pc), float(q.get("high") or lp), float(q.get("low") or lp),
                    int(q.get("volume") or 0), "invezgo", bid=top_bid, ask=top_ask
                )
                _LIVE_QUOTES_CACHE[ticker] = payload
                return payload
        except Exception:
            pass

    # 2. Api.co.id (if API key configured)
    if settings.APICOID_API_KEY:
        try:
            from src.data_collection.apicoid_provider import ApiCoIdProvider
            ac = ApiCoIdProvider()
            q = ac.get_live_quote(ticker)
            if q and (q.get("last_price") or q.get("close")):
                lp = float(q.get("last_price") or q.get("close"))
                pc = float(q.get("previous_close") or lp)
                ob = ac.get_order_book(ticker)
                top_bid = float(ob["bids"][0]["price"]) if ob.get("bids") else None
                top_ask = float(ob["asks"][0]["price"]) if ob.get("asks") else None
                payload = _build_quote_payload(
                    ticker, item, lp, pc,
                    float(q.get("open") or pc), float(q.get("high") or lp), float(q.get("low") or lp),
                    int(q.get("volume") or 0), "apicoid", bid=top_bid, ask=top_ask
                )
                _LIVE_QUOTES_CACHE[ticker] = payload
                return payload
        except Exception:
            pass

    # 3. Yahoo Finance (.JK / ^JKSE)
    try:
        yf_sym = "^JKSE" if ticker in ["^JKSE", "IHSG"] else f"{ticker}.JK"
        t = yf.Ticker(yf_sym)
        fi = getattr(t, "fast_info", None)
        last_price = float(fi["lastPrice"]) if fi and fi.get("lastPrice") else None
        prev_close = float(fi["previousClose"]) if fi and fi.get("previousClose") else None
        volume = int(fi.get("lastVolume", 0) or 0) if fi else 0
        day_open = float(fi.get("open", 0) or 0) if fi else 0.0
        day_high = float(fi.get("dayHigh", 0) or 0) if fi else 0.0
        day_low = float(fi.get("dayLow", 0) or 0) if fi else 0.0

        if not last_price or last_price <= 0:
            hist = t.history(period="5d", interval="1d")
            if hist is not None and not hist.empty:
                last_row = hist.iloc[-1]
                last_price = float(last_row["Close"])
                prev_close = float(hist.iloc[-2]["Close"]) if len(hist) >= 2 else last_price
                day_open = float(last_row.get("Open", prev_close))
                day_high = float(last_row.get("High", last_price))
                day_low = float(last_row.get("Low", last_price))
                volume = int(last_row.get("Volume", 0) or 0)

        if not last_price or last_price <= 0:
            return None

        if not prev_close or prev_close <= 0:
            prev_close = last_price

        payload = _build_quote_payload(
            ticker, item, last_price, prev_close,
            day_open or prev_close, day_high or last_price, day_low or last_price,
            volume, "yahoo_realtime", bid=None, ask=None
        )
        _LIVE_QUOTES_CACHE[ticker] = payload
        return payload
    except Exception:
        return None


# =====================================================================
# Market Overview, Stock Analysis, AI Assistant & Backtest Endpoints
# =====================================================================

@app.get("/api/market/overview")
def get_market_overview(provider_name: Optional[str] = None, db: Session = Depends(get_db)):
    """Mengembalikan ringkasan pasar real-time: IHSG (^JKSE), top gainers, top losers, total volume. Tanpa data DEMO palsu."""
    global _OVERVIEW_CACHE, _OVERVIEW_TIMESTAMP, _LIVE_QUOTES_CACHE
    now = time.time()
    if _OVERVIEW_CACHE and (now - _OVERVIEW_TIMESTAMP < 90.0):
        return _OVERVIEW_CACHE

    # 1. Fetch actual real-time IHSG index from Yahoo Finance (^JKSE)
    ihsg_price = None
    ihsg_change = None
    ihsg_change_pct = None
    ihsg_status = "UNAVAILABLE"
    try:
        t_ihsg = yf.Ticker("^JKSE")
        fi_ihsg = getattr(t_ihsg, "fast_info", None)
        if fi_ihsg and fi_ihsg.get("lastPrice"):
            ihsg_price = round(float(fi_ihsg["lastPrice"]), 2)
            prev_ihsg = float(fi_ihsg.get("previousClose") or ihsg_price)
            ihsg_change = round(ihsg_price - prev_ihsg, 2)
            ihsg_change_pct = round((ihsg_change / prev_ihsg) * 100, 2) if prev_ihsg else 0.0
            ihsg_status = "OPEN"
        else:
            hist_ihsg = t_ihsg.history(period="5d", interval="1d")
            if hist_ihsg is not None and not hist_ihsg.empty:
                ihsg_price = round(float(hist_ihsg["Close"].iloc[-1]), 2)
                prev_ihsg = float(hist_ihsg["Close"].iloc[-2]) if len(hist_ihsg) >= 2 else ihsg_price
                ihsg_change = round(ihsg_price - prev_ihsg, 2)
                ihsg_change_pct = round((ihsg_change / prev_ihsg) * 100, 2) if prev_ihsg else 0.0
                ihsg_status = "OPEN"
    except Exception:
        pass

    # 2. Fetch top liquid IDX tickers from real providers
    top_seeds = [s for s in IDX_MASTER_SEED if s.get("status") == "ACTIVE"][:40]
    quotes = []
    try:
        batch = _batch_fetch_real_quotes_timeseries(top_seeds)
        quotes = list(batch.values())
        for tk, q in batch.items():
            _LIVE_QUOTES_CACHE[tk] = q
    except Exception:
        quotes = []

    if not quotes:
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                quotes = list(filter(None, executor.map(_fetch_single_real_quote, top_seeds[:20])))
        except Exception:
            quotes = []

    total_val = sum(q.get("value", 0.0) for q in quotes)
    gainers = sorted([q for q in quotes if q.get("change_pct", 0) > 0], key=lambda x: x.get("change_pct", 0), reverse=True)[:10]
    losers = sorted([q for q in quotes if q.get("change_pct", 0) < 0], key=lambda x: x.get("change_pct", 0))[:10]

    if not gainers and quotes:
        gainers = sorted(quotes, key=lambda x: x.get("change_pct", 0), reverse=True)[:10]
    if not losers and quotes:
        losers = sorted(quotes, key=lambda x: x.get("change_pct", 0))[:10]

    ai_preview = (
        f"IHSG tercatat di level {ihsg_price:,.2f} ({ihsg_change_pct:+}%) berdasarkan data real-time bursa."
        if ihsg_price is not None
        else "Data IHSG real-time sementara tidak tersedia dari provider."
    )

    overview_data = {
        "ihsg": {
            "name": "IHSG (Jakarta Composite Index)",
            "ticker": "^JKSE",
            "price": ihsg_price,
            "change": ihsg_change,
            "change_pct": ihsg_change_pct,
            "status": ihsg_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        },
        "market_stats": {
            "total_turnover_idr": total_val,
            "monitored_stocks": len(quotes),
            "gainers_count": len([q for q in quotes if q.get("change_pct", 0) > 0]),
            "losers_count": len([q for q in quotes if q.get("change_pct", 0) < 0]),
            "unchanged_count": len([q for q in quotes if q.get("change_pct", 0) == 0])
        },
        "top_gainers": gainers,
        "top_losers": losers,
        "data_available": bool(ihsg_price is not None or quotes),
        "ai_insight_preview": ai_preview,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    if overview_data["data_available"]:
        _OVERVIEW_CACHE = overview_data
        _OVERVIEW_TIMESTAMP = now
    return overview_data


@app.get("/api/analysis/{ticker}")
def get_stock_analysis(ticker: str, timeframe: str = "5m", provider_name: Optional[str] = None):
    """Mengembalikan paket komprehensif analisis saham: Candlestick, TA, ML, dan sinyal."""
    provider = get_data_provider(provider_name)
    quote = provider.get_live_quote(ticker)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
    df = provider.get_intraday_data(ticker, timeframe=timeframe.lower(), limit=100)
    if df.empty or len(df) < 20:
        raise HTTPException(status_code=400, detail="Insufficient intraday candle data")

    df_ta = TechnicalAnalysisEngine.apply_all_indicators(df)
    ta_summary = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
    
    # ML Prediction
    ml_pipeline = ModelPipeline()
    ml_pred = ml_pipeline.predict_latest(df_ta, ticker=ticker, timeframe=timeframe)
    
    # Signal Engine
    sig_engine = ScalpingSignalEngine()
    signal = sig_engine.generate_signal(df, ticker=ticker, timeframe=timeframe)

    # AI Next-Day (T+1) Prediction
    next_day_forecast = next_day_predictor.predict_next_day(
        ticker=ticker,
        df_candles=df,
        quote=quote,
        timeframe=timeframe
    )
    
    # Format candles for TradingView Lightweight Charts
    candles = []
    for _, row in df.iterrows():
        # Support both "timestamp" column and DatetimeIndex
        if "timestamp" in df.columns:
            ts = str(row["timestamp"])
        else:
            ts = str(row.name)
        candles.append({
            "time": ts,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"])
        })
        
    return {
        "ticker": ticker,
        "quote": quote,
        "timeframe": timeframe,
        "candles": candles,
        "technical_indicators": ta_summary,
        "machine_learning": ml_pred,
        "signal": signal,
        "next_day_forecast": next_day_forecast,
        "updated_at": quote.get("timestamp")
    }


@app.get("/api/analysis/predict-next-day/{ticker}")
def get_next_day_prediction(
    ticker: str,
    timeframe: str = Query("5m", description="Timeframe basis analisis"),
    provider_name: Optional[str] = None
):
    """Menghasilkan prediksi komprehensif arah saham (NAIK/TURUN/NETRAL) dan target harga untuk sesi berikutnya (T+1)."""
    clean_ticker = ticker.upper().replace(".JK", "").strip()
    provider = get_data_provider(provider_name)
    quote = provider.get_live_quote(clean_ticker)
    df = provider.get_intraday_data(clean_ticker, timeframe=timeframe.lower(), limit=60)

    # Fallback to Yahoo Finance / cache if empty
    if df.empty or quote is None:
        try:
            t = yf.Ticker(f"{clean_ticker}.JK")
            hist = t.history(interval="5m", period="5d")
            if not hist.empty:
                df = hist.rename(columns={c: c.lower() for c in hist.columns}).tail(60)
                fi = getattr(t, "fast_info", None)
                if fi and "lastPrice" in fi:
                    lp = float(fi["lastPrice"])
                    pc = float(fi.get("previousClose", lp))
                    quote = {
                        "ticker": clean_ticker,
                        "last_price": lp,
                        "previous_close": pc,
                        "change_pct": round(((lp - pc) / pc) * 100, 2) if pc else 0.0,
                        "volume": int(fi.get("lastVolume", 0))
                    }
        except Exception:
            pass

    # If still none, check in _LIVE_QUOTES_CACHE or synthesize
    if quote is None:
        quote = _LIVE_QUOTES_CACHE.get(clean_ticker)
        if not quote:
            match = next((s for s in IDX_MASTER_SEED if s["ticker"] == clean_ticker), None)
            quote = _synthesize_emiten_quote(match or {"ticker": clean_ticker, "sector": "General"})

    res = next_day_predictor.predict_next_day(
        ticker=clean_ticker,
        df_candles=df if not df.empty else None,
        quote=quote,
        timeframe=timeframe
    )
    return res


class AIChatRequest(BaseModel):
    query: str
    ticker_context: Optional[str] = None


@app.post("/api/ai/chat")
def handle_ai_chat(req: AIChatRequest, provider_name: Optional[str] = None, db: Session = Depends(get_db)):
    """Memproses interaksi chat dengan grounding konteks pasar dan indikator."""
    provider = get_data_provider(provider_name)
    
    # 1. Resolve target ticker from context or auto-detect from query across 742 emiten
    target_ticker = (req.ticker_context or "").upper().strip()
    words = req.query.upper().replace("?", " ").replace("!", " ").replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " ").split()
    for w in words:
        clean_w = w.strip()
        if len(clean_w) == 4 and any(s["ticker"] == clean_w for s in IDX_MASTER_SEED):
            target_ticker = clean_w
            break

    if not target_ticker:
        target_ticker = "BBCA"

    context_data = {}
    q = _LIVE_QUOTES_CACHE.get(target_ticker) or provider.get_live_quote(target_ticker)
    df = provider.get_intraday_data(target_ticker, limit=50)

    if q is None:
        match = next((s for s in IDX_MASTER_SEED if s["ticker"] == target_ticker), None)
        q = _synthesize_emiten_quote(match or {"ticker": target_ticker, "sector": "General"})

    if not df.empty:
        df_ta = TechnicalAnalysisEngine.apply_all_indicators(df)
        context_data = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
    else:
        context_data = {
            "rsi_14": q.get("rsi_14", 52.0),
            "relative_volume": q.get("relative_volume", 1.25),
            "vwap": q.get("last_price", 1000),
            "signal": q.get("signal", "BUY")
        }

    context_data["quote"] = q
    try:
        context_data["next_day_forecast"] = next_day_predictor.predict_next_day(
            ticker=target_ticker,
            df_candles=df if not df.empty else None,
            quote=q
        )
    except Exception:
        pass

    sim = PaperTradingSimulator(db_session=db)
    portfolio = sim.get_portfolio_summary()

    # Pass top screened stocks for broader multi-stock context
    top_screened = _REAL_SCREENER_CACHE[:10] if _REAL_SCREENER_CACHE else []

    chat_assistant = AIChatAssistant()
    reply = chat_assistant.answer_query(
        user_query=req.query,
        current_market_context=context_data,
        screened_stocks=top_screened,
        portfolio_summary=portfolio
    )
    return {"reply": reply, "active_ticker": target_ticker}


@app.get("/api/ai/decision/{ticker}")
def get_ai_decision(ticker: str, timeframe: str = "5m", provider_name: Optional[str] = None):
    """Menghasilkan analisis keputusan trading AI yang divalidasi oleh gatekeeper kuantitatif."""
    provider = get_data_provider(provider_name)
    quote = provider.get_live_quote(ticker)
    df = provider.get_intraday_data(ticker, timeframe=timeframe.lower(), limit=60)
    if df.empty or len(df) < 20:
        raise HTTPException(status_code=400, detail="Data candle tidak mencukupi untuk evaluasi AI")

    engine = AITradingDecisionEngine()
    decision = engine.analyze_stock(ticker=ticker, df_candles=df, quote=quote, timeframe=timeframe)
    return decision


class BacktestRequest(BaseModel):
    ticker: str
    strategy: Optional[str] = "Scalping_V1"
    initial_capital: Optional[float] = 10_000_000.0
    slippage_ticks: Optional[int] = 1


@app.post("/api/backtest/run")
def run_backtest_simulation(req: BacktestRequest, provider_name: Optional[str] = None):
    """Menjalankan simulasi walk-forward backtest pada candle intraday."""
    clean_ticker = req.ticker.upper().replace(".JK", "").strip()
    provider = get_data_provider(provider_name)
    df = provider.get_intraday_data(clean_ticker, timeframe="5m", limit=150)
    if df.empty or len(df) < 30:
        from src.data_collection.mock_provider import MockDataProvider
        df = MockDataProvider().get_intraday_data(clean_ticker, timeframe="5m", limit=150)
    if df.empty or len(df) < 30:
        raise HTTPException(status_code=400, detail=f"Insufficient intraday candles to backtest {clean_ticker}")

    engine = BacktestEngine(
        initial_capital=req.initial_capital or 10_000_000.0,
        slippage_ticks=req.slippage_ticks or 1
    )
    result = engine.run_backtest(df_candles=df, ticker=clean_ticker, strategy_name=req.strategy)
    return result


# =====================================================================
# Dedicated Real IDX Market Endpoints (Yahoo Finance .JK)
# =====================================================================

def _batch_fetch_real_quotes_timeseries(seed_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Batch-fetch real 1-month daily time-series OHLCV from Yahoo Finance (.JK) for fast, accurate screener quotes."""
    results: Dict[str, Dict[str, Any]] = {}
    if not seed_items:
        return results

    seed_map = {s["ticker"]: s for s in seed_items}
    chunk_size = 120
    for start in range(0, len(seed_items), chunk_size):
        chunk = seed_items[start : start + chunk_size]
        jk_tickers = [f"{s['ticker']}.JK" for s in chunk]
        try:
            df_all = yf.download(
                jk_tickers,
                period="1mo",
                interval="1d",
                group_by="ticker",
                threads=True,
                progress=False,
            )
            if df_all is None or df_all.empty:
                continue

            is_multi = isinstance(df_all.columns, pd.MultiIndex)
            for s in chunk:
                ticker = s["ticker"]
                jk = f"{ticker}.JK"
                try:
                    sub = df_all[jk] if is_multi else df_all
                    sub = sub.dropna(subset=["Close"])
                    if sub.empty or len(sub) < 2:
                        continue

                    last_row = sub.iloc[-1]
                    prev_row = sub.iloc[-2]
                    last_price = round(float(last_row["Close"]), 0)
                    prev_close = round(float(prev_row["Close"]), 0)
                    if last_price <= 0:
                        continue

                    day_open = round(float(last_row.get("Open", prev_close)), 0)
                    day_high = round(float(last_row.get("High", last_price)), 0)
                    day_low = round(float(last_row.get("Low", last_price)), 0)
                    volume = int(last_row.get("Volume", 0) or 0)

                    avg_vol = float(sub["Volume"].iloc[:-1].mean()) if len(sub) > 2 else float(volume or 1)
                    rel_vol = round(max(0.1, min(5.0, (volume / avg_vol) if avg_vol > 0 else 1.0)), 2)

                    rsi_series = TechnicalAnalysisEngine.calculate_rsi(sub["Close"], period=14)
                    rsi_val = float(rsi_series.iloc[-1]) if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]) else 50.0
                    rsi_est = round(max(5.0, min(95.0, rsi_val)), 1)

                    change = round(last_price - prev_close, 2)
                    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

                    if change_pct >= 1.5 and rel_vol >= 1.1:
                        signal = "BUY"
                        score = min(96, int(72 + change_pct * 3 + rel_vol * 4))
                    elif change_pct <= -1.8:
                        signal = "SELL"
                        score = max(20, int(42 + change_pct * 4))
                    elif change_pct > 0:
                        signal = "BUY" if rel_vol >= 1.3 else "HOLD"
                        score = min(90, int(58 + change_pct * 2 + rel_vol * 3))
                    else:
                        signal = "HOLD"
                        score = max(35, int(48 + change_pct * 2))

                    if change_pct >= 0.8 or (score >= 65 and rel_vol >= 1.05):
                        next_day_dir = "NAIK"
                        next_day_prob = min(88, int(60 + change_pct * 3 + (score - 60) * 0.4))
                    elif change_pct <= -1.0 or score <= 40:
                        next_day_dir = "TURUN"
                        next_day_prob = min(85, int(60 + abs(change_pct) * 3 + (50 - score) * 0.5))
                    else:
                        next_day_dir = "NETRAL"
                        next_day_prob = 52

                    item = seed_map[ticker]
                    results[ticker] = {
                        "ticker": ticker,
                        "name": item.get("name", f"{ticker} Tbk"),
                        "sector": item.get("sector", "General"),
                        "board": item.get("board", "Utama"),
                        "last_price": align_to_tick(last_price),
                        "open": align_to_tick(day_open),
                        "high": align_to_tick(day_high),
                        "low": align_to_tick(day_low),
                        "previous_close": align_to_tick(prev_close),
                        "change": change,
                        "change_pct": change_pct,
                        "volume": volume,
                        "value": volume * last_price,
                        "relative_volume": rel_vol,
                        "rsi_14": rsi_est,
                        "signal": signal,
                        "scalping_score": score,
                        "next_day_direction": next_day_dir,
                        "next_day_probability": next_day_prob,
                        "status": item.get("status", "ACTIVE"),
                        "data_source": "yahoo_realtime",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                except Exception:
                    continue
        except Exception:
            continue

    return results


@app.get("/api/real-screener")
def get_real_market_screener(
    sector: Optional[str] = Query(None, description="Filter sector"),
    min_rel_vol: Optional[float] = Query(0.0),
    next_day_pred: Optional[str] = Query(None, description="Filter prediksi besok: ALL, NAIK, TURUN, NETRAL"),
    limit: Optional[int] = Query(800, ge=10, le=1000),
    force_refresh: bool = False
):
    """Scan real IDX stocks from the entire 742 universe using live Yahoo Finance (.JK) batch time-series and full master data."""
    global _REAL_SCREENER_CACHE, _REAL_SCREENER_TIMESTAMP, _LIVE_QUOTES_CACHE
    now = time.time()

    # Rebuild full universe if expired or empty
    if force_refresh or not _REAL_SCREENER_CACHE or (now - _REAL_SCREENER_TIMESTAMP > 180.0):
        # 1. Batch-fetch real 1-month time-series & latest quotes for top 240 active stocks
        active_seeds = [s for s in IDX_MASTER_SEED if s.get("status") in ["ACTIVE", "NEWLY_LISTED"]][:240]
        try:
            batch_quotes = _batch_fetch_real_quotes_timeseries(active_seeds)
            for tk, q in batch_quotes.items():
                _LIVE_QUOTES_CACHE[tk] = q
        except Exception:
            pass

        # 2. Build universe ONLY from real provider quotes (never mix synthetic prices into real screener)
        full_universe = []
        for s in IDX_MASTER_SEED:
            ticker = s["ticker"]
            if ticker in _LIVE_QUOTES_CACHE:
                q_item = dict(_LIVE_QUOTES_CACHE[ticker])
                if q_item.get("data_source") in ("invezgo", "apicoid", "yahoo_realtime"):
                    full_universe.append(q_item)

        full_universe.sort(key=lambda x: x["scalping_score"], reverse=True)
        if full_universe:
            _REAL_SCREENER_CACHE = full_universe
            _REAL_SCREENER_TIMESTAMP = now

    results = _REAL_SCREENER_CACHE

    if sector and sector != "ALL":
        results = [r for r in results if r["sector"].lower() == sector.lower()]
    if min_rel_vol and min_rel_vol > 0.0:
        results = [r for r in results if r.get("relative_volume", 0) >= min_rel_vol]
    if next_day_pred and next_day_pred != "ALL":
        results = [r for r in results if r.get("next_day_direction", "").upper() == next_day_pred.upper()]

    if limit and limit > 0:
        results = results[:limit]

    return {
        "count": len(results),
        "total_universe": len(IDX_MASTER_SEED),
        "results": results,
        "cached_at": _REAL_SCREENER_TIMESTAMP
    }


@app.get("/api/real-quotes")
def get_real_quotes(tickers: str = Query("BBCA,BBRI,BMRI,TLKM,ASII,MEDC,ADRO,GOTO,BRIS,AMMN")):
    """Fetch live market quotes directly for specific IDX tickers."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    items = []
    for sym in ticker_list:
        if sym in ["IHSG", "^JKSE"]:
            items.append({"ticker": "^JKSE", "name": "Indeks Harga Saham Gabungan", "sector": "Composite", "board": "Utama"})
        else:
            match = next((s for s in IDX_MASTER_SEED if s["ticker"] == sym), None)
            items.append(match or {"ticker": sym, "name": f"{sym} Indonesia Tbk", "sector": "General", "board": "Utama"})

    with ThreadPoolExecutor(max_workers=10) as executor:
        quotes = list(filter(None, executor.map(_fetch_single_real_quote, items)))

    return {"count": len(quotes), "results": quotes}


@app.get("/api/real-history/{ticker}")
def get_real_stock_history(
    ticker: str,
    timeframe: str = Query("5m", description="1m, 5m, 15m, 1h, 1d"),
    limit: int = Query(60, ge=10, le=200)
):
    """Fetch real historical OHLCV time-series candles with technical indicators for TradingView/Chart.js."""
    clean_ticker = ticker.upper().replace(".JK", "").strip()
    is_ihsg = clean_ticker in ["IHSG", "^JKSE", "COMPOSITE"]
    if is_ihsg:
        clean_ticker = "IHSG"
        formatted = "^JKSE"
    else:
        formatted = f"{clean_ticker}.JK"

    tf_key = timeframe.lower().strip()
    tf_map = {
        "1m": ("1m", "5d"),
        "5m": ("5m", "5d"),
        "15m": ("15m", "1mo"),
        "1h": ("60m", "1mo"),
        "1d": ("1d", "6mo")
    }
    interval, period = tf_map.get(tf_key, ("5m", "5d"))

    # Per-ticker & per-timeframe cache (60s TTL, never caches synthetic data)
    global _HISTORY_CACHE
    if "_HISTORY_CACHE" not in globals():
        _HISTORY_CACHE = {}
    cache_key = (clean_ticker, tf_key, limit)
    now_ts = time.time()
    cached = _HISTORY_CACHE.get(cache_key)
    if cached and (now_ts - cached.get("_cached_at", 0) < 60.0):
        return cached["payload"]

    df = pd.DataFrame()
    data_source = "yahoo_realtime"
    t = None

    # 1. Invezgo API (if API key configured and not IHSG)
    if not is_ihsg and settings.INVEZGO_API_KEY:
        try:
            from src.data_collection.invezgo_provider import InvezgoProvider
            inv = InvezgoProvider()
            inv_df = inv.get_daily_history(clean_ticker) if tf_key == "1d" else inv.get_intraday_data(clean_ticker, timeframe=tf_key, limit=limit)
            if inv_df is not None and not inv_df.empty:
                df = inv_df.tail(limit).copy()
                data_source = "invezgo"
        except Exception:
            df = pd.DataFrame()

    # 2. Api.co.id (if API key configured and not IHSG)
    if df.empty and not is_ihsg and settings.APICOID_API_KEY:
        try:
            from src.data_collection.apicoid_provider import ApiCoIdProvider
            ac = ApiCoIdProvider()
            ac_df = ac.get_daily_history(clean_ticker) if tf_key == "1d" else ac.get_intraday_data(clean_ticker, timeframe=tf_key, limit=limit)
            if ac_df is not None and not ac_df.empty:
                df = ac_df.tail(limit).copy()
                data_source = "apicoid"
        except Exception:
            df = pd.DataFrame()

    # 3. Yahoo Finance (.JK / ^JKSE)
    if df.empty:
        try:
            t = yf.Ticker(formatted)
            hist = t.history(interval=interval, period=period)
            if hist is not None and not hist.empty:
                df = hist.tail(limit).copy().reset_index()
                data_source = "yahoo_realtime"
        except Exception:
            df = pd.DataFrame()

    if df.empty:
        raise HTTPException(
            status_code=503,
            detail=f"Data historis real-time untuk {clean_ticker} ({tf_key}) tidak tersedia dari provider saat ini."
        )

    # Normalize column names safely
    col_map = {c: c.lower() for c in df.columns}
    df_norm = df.rename(columns=col_map)
    date_col = "datetime" if "datetime" in df_norm.columns else ("date" if "date" in df_norm.columns else ("timestamp" if "timestamp" in df_norm.columns else df_norm.columns[0]))

    df_norm = df_norm.dropna(subset=["close"]).reset_index(drop=True)
    if df_norm.empty:
        raise HTTPException(
            status_code=503,
            detail=f"Data candle untuk {clean_ticker} ({tf_key}) kosong dari provider."
        )

    close_series = df_norm["close"].astype(float)
    ema20 = TechnicalAnalysisEngine.calculate_ema(close_series, span=20)
    ema50 = TechnicalAnalysisEngine.calculate_ema(close_series, span=50)
    rsi = TechnicalAnalysisEngine.calculate_rsi(close_series, period=14)

    candles = []
    labels = []
    prices = []
    ema20_vals = []
    ema50_vals = []

    for i, row in df_norm.iterrows():
        ts_str = str(row[date_col])
        if " " in ts_str:
            time_label = ts_str.split(" ")[1][:5]
        elif "T" in ts_str:
            time_label = ts_str.split("T")[1][:5]
        else:
            time_label = ts_str[:10]

        op = round(float(row["open"]), 2 if is_ihsg else 0)
        hi = round(float(row["high"]), 2 if is_ihsg else 0)
        lo = round(float(row["low"]), 2 if is_ihsg else 0)
        cl = round(float(row["close"]), 2 if is_ihsg else 0)
        vol = int(row.get("volume", 0) or 0)

        candles.append({
            "time": ts_str,
            "label": time_label,
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl,
            "volume": vol
        })
        labels.append(time_label)
        prices.append(cl)
        ema20_vals.append(round(float(ema20.iloc[i]), 2) if not pd.isna(ema20.iloc[i]) else cl)
        ema50_vals.append(round(float(ema50.iloc[i]), 2) if not pd.isna(ema50.iloc[i]) else cl)

    fi = getattr(t, "fast_info", None) if t is not None else None
    raw_last = float(fi["lastPrice"]) if fi and fi.get("lastPrice") else (prices[-1] if prices else 0.0)
    raw_prev = float(fi["previousClose"]) if fi and fi.get("previousClose") else (prices[-2] if len(prices) >= 2 else raw_last)

    if is_ihsg:
        last_price = round(raw_last, 2)
        prev_close = round(raw_prev, 2)
    else:
        last_price = align_to_tick(round(raw_last, 0))
        prev_close = align_to_tick(round(raw_prev, 0))

    if prices:
        prices[-1] = last_price
        candles[-1]["close"] = last_price

    change = round(last_price - prev_close, 2)
    change_pct = round(((last_price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
    avg_vol = float(df_norm["volume"].iloc[:-1].mean()) if len(df_norm) > 2 else float(candles[-1]["volume"] or 1)
    latest_vol = int(candles[-1]["volume"]) if candles else 0
    rel_vol = round(max(0.1, min(5.0, (latest_vol / avg_vol) if avg_vol > 0 else 1.0)), 2)
    vwap_raw = float((df_norm["close"].astype(float) * df_norm["volume"].astype(float)).sum() / max(1.0, df_norm["volume"].astype(float).sum()))
    vwap_val = round(vwap_raw, 2) if is_ihsg else align_to_tick(round(vwap_raw, 0))

    payload = {
        "ticker": clean_ticker,
        "timeframe": tf_key,
        "last_price": last_price,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "volume": latest_vol,
        "value": latest_vol * last_price,
        "relative_volume": rel_vol,
        "vwap": vwap_val if vwap_val > 0 else last_price,
        "candles": candles,
        "labels": labels,
        "prices": prices,
        "ema20": ema20_vals,
        "ema50": ema50_vals,
        "rsi_14": round(float(rsi.iloc[-1]), 1) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else None,
        "data_source": data_source,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    _HISTORY_CACHE[cache_key] = {"_cached_at": now_ts, "payload": payload}
    return payload


# Mount modern Fintech SaaS Web Frontend
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="static_web")

