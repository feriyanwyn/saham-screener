"""Unit tests for Risk Management Engine."""
from src.risk_management.risk_manager import RiskManager
from config.idx_constants import LOT_SIZE


def test_fee_calculation():
    rm = RiskManager(capital=10_000_000)
    
    # Beli Rp 10 Juta
    buy_fees = rm.calculate_fees(10_000_000, is_buy=True)
    # Broker: 15.000, PPN: 1.650, Levy: 4.300 -> Total: 20.950 (~0.21%)
    assert buy_fees["fee_broker"] == 15000.0
    assert buy_fees["tax_ppn"] == 1650.0
    assert buy_fees["fee_levy"] == 4300.0
    assert buy_fees["total_fee"] == 20950.0
    assert buy_fees["net_amount"] == 10_020_950.0

    # Jual Rp 10 Juta
    sell_fees = rm.calculate_fees(10_000_000, is_buy=False)
    # Broker: 25.000, PPN: 2.750, Levy: 4.300, PPh: 10.000 -> Total: 42.050 (~0.42%)
    assert sell_fees["fee_broker"] == 25000.0
    assert sell_fees["tax_ppn"] == 2750.0
    assert sell_fees["fee_levy"] == 4300.0
    assert sell_fees["tax_pph"] == 10000.0
    assert sell_fees["total_fee"] == 42050.0
    assert sell_fees["net_amount"] == 9_957_950.0


def test_position_sizing_lot_rounding():
    rm = RiskManager(capital=10_000_000, max_risk_pct=0.015)
    # Max risk = Rp 150.000
    # Entry 1000, SL 950 -> Risk per share = 50
    # Max shares = 150.000 / 50 = 3000 shares = 30 lots
    sizing = rm.calculate_position_size(entry_price=1000, stop_loss=950, available_cash=10_000_000)
    assert sizing["is_valid"] is True
    assert sizing["lots"] <= 30
    assert sizing["shares"] % LOT_SIZE == 0
