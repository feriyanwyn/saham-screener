"""Full Market Scanner & Sector Scanner Engine for Indonesia Stock Exchange (IDX).
Mendukung:
1. Pemindaian seluruh pasar saham BEI atau per sektor tertentu.
2. Pengecekan kelengkapan data kuantitatif.
3. Eksekusi Technical Indicators & Model Deep Learning (LSTM & BiLSTM).
4. Penentuan Sinyal Kuantitatif (BUY, SELL, HOLD, WATCHLIST).
5. Kategorisasi AI Stock Ranking:
   - TOP_BULLISH, TOP_BEARISH, HIGHEST_VOLUME, STRONGEST_MOMENTUM, LOWEST_RISK, POTENTIAL_SCALPING.
6. Penyimpanan hasil scan di database (caching) untuk akses instan.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from config.idx_constants import align_to_tick, get_tick_size, get_ara_arb_limits
from database.connection import SessionLocal
from database.models import Instrument, MarketScanResult
from src.data_collection.base_provider import BaseDataProvider
from src.technical_analysis.indicators import TechnicalAnalysisEngine
from src.machine_learning.trainer import ModelPipeline


class FullMarketScanner:
    """Full IDX Market & Sector Scanning Engine with persistent caching."""

    def __init__(
        self,
        provider: BaseDataProvider,
        ml_pipeline: Optional[ModelPipeline] = None,
        db_session: Optional[Session] = None
    ):
        self.provider = provider
        self.ml_pipe = ml_pipeline or ModelPipeline()
        self.db = db_session or SessionLocal()

    def run_scan(
        self,
        sector_filter: Optional[str] = None,
        max_stocks: Optional[int] = None,
        timeframe: str = "5m"
    ) -> Dict[str, Any]:
        """Menjalankan full market scan atau scan sektoral secara terstruktur."""
        scan_id = f"SCAN-{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.utcnow()

        # 1. Ambil daftar ticker target dari master database
        query = self.db.query(Instrument).filter(Instrument.is_active == True, Instrument.is_suspended == False)
        if sector_filter and sector_filter.upper() != "ALL":
            query = query.filter(Instrument.sector == sector_filter)

        instruments = query.all()
        if max_stocks:
            instruments = instruments[:max_stocks]

        total_target = len(instruments)
        scanned_items = []
        sufficient_data_count = 0

        for inst in instruments:
            ticker = inst.ticker
            name = inst.name
            sector = inst.sector or "General"

            # Ambil data intraday dari provider
            df_intraday = self.provider.get_intraday_data(ticker, timeframe=timeframe, limit=60)
            quote = self.provider.get_live_quote(ticker)

            has_sufficient = not df_intraday.empty and len(df_intraday) >= 15
            if has_sufficient:
                sufficient_data_count += 1
                df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_intraday)
                ta = TechnicalAnalysisEngine.get_latest_signals_summary(df_ta)
                last_price = ta["close"]
                change_pct = quote.get("change_pct", 0.0) if quote else 0.0
                volume = quote.get("volume", int(df_intraday["volume"].sum())) if quote else int(df_intraday["volume"].sum())
                value = quote.get("value", volume * last_price) if quote else volume * last_price

                # Deep Learning prediction
                ml_pred = self.ml_pipe.predict_latest(df_ta, ticker=ticker, timeframe=timeframe.upper())
                pred_return = ml_pred.get("predicted_return", 0.0)
                up_prob = ml_pred.get("up_probability", 0.5)
                conf = ml_pred.get("calibrated_confidence", 0.5)

                # Scoring
                tech_score = 0.0
                rsi = ta.get("rsi_14", 50.0)
                if 45 <= rsi <= 65:
                    tech_score += 25.0
                if ta.get("is_above_vwap"):
                    tech_score += 25.0
                if ta.get("is_macd_bullish"):
                    tech_score += 20.0
                if ta.get("relative_volume", 1.0) >= 1.2:
                    tech_score += 15.0
                if ta.get("is_uptrend"):
                    tech_score += 15.0
                tech_score = min(100.0, tech_score)

                # Sinyal Kuantitatif
                if (up_prob >= 0.55 or pred_return >= 0.005) and ta.get("is_above_vwap") and (42 <= rsi <= 68):
                    signal_type = "BUY"
                elif rsi >= 75 or (not ta.get("is_above_vwap") and up_prob < 0.42):
                    signal_type = "SELL"
                elif ta.get("relative_volume", 1.0) >= 1.4:
                    signal_type = "WATCHLIST"
                else:
                    signal_type = "HOLD"

                # Kategori AI Ranking
                rel_vol = ta.get("relative_volume", 1.0)
                if ta.get("is_uptrend") and ta.get("is_above_vwap") and rsi > 50 and up_prob >= 0.52:
                    ranking_cat = "TOP_BULLISH"
                elif not ta.get("is_above_vwap") and rsi < 42 and up_prob < 0.45:
                    ranking_cat = "TOP_BEARISH"
                elif rel_vol >= 1.6:
                    ranking_cat = "HIGHEST_VOLUME"
                elif 50 <= rsi <= 65 and ta.get("macd_crossover"):
                    ranking_cat = "STRONGEST_MOMENTUM"
                elif value >= 5_000_000_000 and (ta.get("atr_14", 10.0) / last_price) < 0.02:
                    ranking_cat = "LOWEST_RISK"
                elif signal_type == "BUY" and tech_score >= 65:
                    ranking_cat = "POTENTIAL_SCALPING"
                else:
                    ranking_cat = "POTENTIAL_SCALPING" if signal_type == "BUY" else "NEUTRAL"

                item_res = {
                    "scan_id": scan_id,
                    "ticker": ticker,
                    "name": name,
                    "sector": sector,
                    "last_price": last_price,
                    "change_pct": change_pct,
                    "volume": volume,
                    "value": value,
                    "rsi_14": rsi,
                    "macd": ta.get("macd", 0.0),
                    "is_above_vwap": ta.get("is_above_vwap", False),
                    "lstm_predicted_return": pred_return,
                    "bilstm_direction_prob": up_prob,
                    "signal_type": signal_type,
                    "technical_score": round(tech_score, 1),
                    "ai_confidence": round(conf, 3),
                    "ranking_category": ranking_cat,
                    "has_sufficient_data": True
                }
            else:
                # Saham tanpa data memadai
                lp = quote.get("last_price", 0.0) if quote else 0.0
                item_res = {
                    "scan_id": scan_id,
                    "ticker": ticker,
                    "name": name,
                    "sector": sector,
                    "last_price": lp,
                    "change_pct": 0.0,
                    "volume": 0,
                    "value": 0.0,
                    "rsi_14": None,
                    "macd": None,
                    "is_above_vwap": False,
                    "lstm_predicted_return": None,
                    "bilstm_direction_prob": None,
                    "signal_type": "NO_DATA",
                    "technical_score": 0.0,
                    "ai_confidence": 0.0,
                    "ranking_category": "NO_DATA",
                    "has_sufficient_data": False
                }

            scanned_items.append(item_res)

        # 2. Urutkan berdasarkan Technical Score tertinggi & berikan Opportunity Rank
        valid_items = [s for s in scanned_items if s["has_sufficient_data"]]
        valid_items.sort(key=lambda x: (x["technical_score"], x["ai_confidence"]), reverse=True)
        for rank_idx, itm in enumerate(valid_items, 1):
            itm["opportunity_rank"] = rank_idx

        # 3. Simpan ke Database (Persistent Cache)
        try:
            for itm in scanned_items:
                record = MarketScanResult(
                    scan_id=scan_id,
                    ticker=itm["ticker"],
                    name=itm["name"],
                    sector=itm["sector"],
                    last_price=itm["last_price"],
                    change_pct=itm["change_pct"],
                    volume=itm["volume"],
                    value=itm["value"],
                    rsi_14=itm["rsi_14"],
                    macd=itm["macd"],
                    is_above_vwap=itm["is_above_vwap"],
                    lstm_predicted_return=itm["lstm_predicted_return"],
                    bilstm_direction_prob=itm["bilstm_direction_prob"],
                    signal_type=itm["signal_type"],
                    technical_score=itm["technical_score"],
                    ai_confidence=itm["ai_confidence"],
                    opportunity_rank=itm.get("opportunity_rank", 0),
                    ranking_category=itm["ranking_category"],
                    has_sufficient_data=itm["has_sufficient_data"],
                    scanned_at=start_time
                )
                self.db.add(record)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"[FullMarketScanner] Error caching scan results: {e}")

        elapsed_sec = (datetime.utcnow() - start_time).total_seconds()

        return {
            "scan_id": scan_id,
            "sector_filter": sector_filter or "ALL",
            "total_scanned": total_target,
            "sufficient_data_count": sufficient_data_count,
            "elapsed_seconds": round(elapsed_sec, 2),
            "top_candidates": valid_items[:15],
            "total_valid_results": len(valid_items)
        }

    def get_latest_cached_scan(
        self,
        category: Optional[str] = None,
        sector: Optional[str] = None,
        signal_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Mengambil hasil scan terbaru dari cache database tanpa melakukan pemindaian ulang."""
        # Ambil scan_id terbaru
        latest = (
            self.db.query(MarketScanResult.scan_id)
            .order_by(MarketScanResult.scanned_at.desc())
            .first()
        )
        if not latest:
            return []

        latest_id = latest[0]
        query = self.db.query(MarketScanResult).filter(MarketScanResult.scan_id == latest_id)

        if category and category.upper() != "ALL":
            query = query.filter(MarketScanResult.ranking_category == category.upper())
        if sector and sector.upper() != "ALL":
            query = query.filter(MarketScanResult.sector == sector)
        if signal_type and signal_type.upper() != "ALL":
            query = query.filter(MarketScanResult.signal_type == signal_type.upper())

        query = query.order_by(MarketScanResult.technical_score.desc()).limit(limit)
        records = query.all()

        results = []
        for r in records:
            results.append({
                "ticker": r.ticker,
                "name": r.name,
                "sector": r.sector,
                "last_price": r.last_price,
                "change_pct": r.change_pct,
                "volume": r.volume,
                "value": r.value,
                "rsi_14": r.rsi_14,
                "macd": r.macd,
                "is_above_vwap": r.is_above_vwap,
                "signal_type": r.signal_type,
                "technical_score": r.technical_score,
                "opportunity_rank": r.opportunity_rank,
                "ranking_category": r.ranking_category,
                "scanned_at": r.scanned_at.strftime("%Y-%m-%d %H:%M")
            })

        return results
