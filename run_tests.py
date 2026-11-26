"""Test runner executing all test suites without external pytest dependency."""
import sys
import unittest

# Import tests
from tests.test_idx_constants import test_lot_size, test_tick_sizes, test_align_to_tick, test_ara_arb_limits
from tests.test_risk_management import test_fee_calculation, test_position_sizing_lot_rounding
from tests.test_paper_trading import test_paper_trading_lifecycle
from tests.test_technical_analysis import sample_ohlcv, test_rsi_calculation, test_macd_calculation, test_apply_all_indicators
from tests.test_ai_assistant import (
    test_validator_approves_valid_buy,
    test_validator_rejects_poor_rr,
    test_ai_decision_engine_mock,
    test_ai_chat_assistant
)
from tests.test_full_idx_coverage import (
    test_idx_master_database_seeding,
    test_coverage_statistics,
    test_market_explorer_query_and_pagination,
    test_full_market_scanner_and_caching
)


class IDXScalperTestSuite(unittest.TestCase):
    def test_01_lot_size(self):
        test_lot_size()

    def test_02_tick_sizes(self):
        test_tick_sizes()

    def test_03_align_to_tick(self):
        test_align_to_tick()

    def test_04_ara_arb_limits(self):
        test_ara_arb_limits()

    def test_05_fee_calculation(self):
        test_fee_calculation()

    def test_06_position_sizing(self):
        test_position_sizing_lot_rounding()

    def test_07_paper_trading(self):
        test_paper_trading_lifecycle()

    def test_08_technical_indicators(self):
        df = sample_ohlcv()
        test_rsi_calculation(df)
        test_macd_calculation(df)
        test_apply_all_indicators(df)

    def test_09_ai_validator(self):
        test_validator_approves_valid_buy()
        test_validator_rejects_poor_rr()

    def test_10_ai_decision_and_chat(self):
        test_ai_decision_engine_mock()
        test_ai_chat_assistant()

    def test_11_idx_master_database_seeding(self):
        test_idx_master_database_seeding()

    def test_12_coverage_statistics(self):
        test_coverage_statistics()

    def test_13_market_explorer_query_and_pagination(self):
        test_market_explorer_query_and_pagination()

    def test_14_full_market_scanner_and_caching(self):
        test_full_market_scanner_and_caching()


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(IDXScalperTestSuite)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
