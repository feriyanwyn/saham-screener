"""Integration tests for Paper Trading Simulator."""
from src.paper_trading.account import PaperTradingSimulator
from database.connection import init_db


def test_paper_trading_lifecycle():
    init_db()
    sim = PaperTradingSimulator("UNITTEST_ACC", initial_balance=10_000_000)

    # 1. Beli 2 Lot BBCA pada harga Rp9.850
    buy_res = sim.execute_buy(
        ticker="BBCA",
        price=9850,
        lots=2,
        stop_loss=9700,
        take_profit=10100
    )
    assert buy_res["status"] == "FILLED"
    assert buy_res["lots"] == 2

    summary = sim.get_portfolio_summary()
    assert summary["cash"] < 10_000_000
    assert len(summary["open_positions"]) == 1
    assert summary["open_positions"][0]["ticker"] == "BBCA"

    # 2. Jual 2 Lot BBCA pada harga profit Rp9.950
    sell_res = sim.execute_sell(
        ticker="BBCA",
        price=9950,
        lots=2
    )
    assert sell_res["status"] == "FILLED"
    assert sell_res["realized_pnl"] > 0

    final_summary = sim.get_portfolio_summary()
    assert len(final_summary["open_positions"]) == 0
    assert final_summary["cash"] > 10_000_000
