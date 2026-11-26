"""Unit and integration tests for Full IDX Stock Coverage, Market Explorer, and Full Market Scanner."""
from database.connection import init_db, SessionLocal
from database.models import Instrument, MarketScanResult
from src.data_collection.idx_master_data import seed_idx_master_database, get_idx_coverage_stats
from src.data_collection.universe_manager import UniverseManager
from src.data_collection.mock_provider import MockDataProvider
from src.stock_screener.full_market_scanner import FullMarketScanner


def test_idx_master_database_seeding():
    init_db()
    db = SessionLocal()
    count = seed_idx_master_database(db, force_refresh=True)
    assert count >= 60  # Seed master data mencakup seluruh sektor BEI
    db.close()


def test_coverage_statistics():
    db = SessionLocal()
    stats = get_idx_coverage_stats(db)
    assert stats["total_listed_idx"] >= 60
    assert stats["active_stocks"] > 0
    assert stats["suspended_stocks"] > 0
    assert stats["newly_listed_stocks"] > 0
    assert stats["delisted_stocks"] > 0
    assert "Financials" in stats["sectors_distribution"]
    assert "Energy" in stats["sectors_distribution"]
    assert stats["coverage_breakdown"]["has_sufficient_daily_data"] > 0
    db.close()


def test_market_explorer_query_and_pagination():
    db = SessionLocal()
    mgr = UniverseManager(db_session=db)

    # 1. Test Search by Ticker
    res_ticker = mgr.get_explorer_stocks(search="BBCA")
    assert res_ticker["total_items"] >= 1
    assert res_ticker["items"][0]["ticker"] == "BBCA"

    # 2. Test Sector Filter
    res_fin = mgr.get_explorer_stocks(sector="Financials")
    assert res_fin["total_items"] >= 5
    for itm in res_fin["items"]:
        assert itm["sector"] == "Financials"

    # 3. Test Status Filter (SUSPENDED)
    res_susp = mgr.get_explorer_stocks(status="SUSPENDED")
    assert res_susp["total_items"] >= 1
    for itm in res_susp["items"]:
        assert itm["status"] == "SUSPENDED"

    # 4. Test Pagination
    res_page = mgr.get_explorer_stocks(page=1, page_size=10)
    assert len(res_page["items"]) <= 10
    assert res_page["total_pages"] >= 1
    db.close()


def test_full_market_scanner_and_caching():
    db = SessionLocal()
    provider = MockDataProvider()
    scanner = FullMarketScanner(provider=provider, db_session=db)

    # Run scan on 10 stocks
    scan_res = scanner.run_scan(max_stocks=10)
    assert scan_res["total_scanned"] == 10
    assert scan_res["sufficient_data_count"] > 0
    assert len(scan_res["top_candidates"]) > 0

    # Test retrieval from DB cache
    cached = scanner.get_latest_cached_scan(limit=10)
    assert len(cached) > 0
    assert "ticker" in cached[0]
    assert "technical_score" in cached[0]
    db.close()
