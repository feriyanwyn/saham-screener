"""Risk Management Engine for Indonesian Stock Market (IDX).
Mengatur kalkulasi position sizing per lot, batasan risiko per transaksi,
maksimum kerugian harian, batasan eksposur portofolio, dan perhitungan komisi broker/pajak resmi.
"""
from typing import Dict, Any, Tuple
from config.idx_constants import LOT_SIZE, align_to_tick, get_tick_size, get_ara_arb_limits
from config.settings import settings


class RiskManager:
    """Quantitative risk engine enforcing Indonesian exchange regulations and capital preservation."""

    def __init__(
        self,
        capital: float = settings.INITIAL_CAPITAL_IDR,
        max_risk_pct: float = settings.MAX_RISK_PER_TRADE_PCT,
        max_daily_loss_pct: float = settings.MAX_DAILY_LOSS_PCT,
        max_positions: int = settings.MAX_OPEN_POSITIONS,
        buy_fee_pct: float = settings.BROKER_BUY_FEE_PCT,
        sell_fee_pct: float = settings.BROKER_SELL_FEE_PCT
    ):
        self.capital = capital
        self.max_risk_pct = max_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions
        self.buy_fee_pct = buy_fee_pct
        self.sell_fee_pct = sell_fee_pct

    def calculate_fees(self, gross_amount: float, is_buy: bool = True) -> Dict[str, float]:
        """Menghitung rincian biaya transaksi sesuai regulasi BEI."""
        if is_buy:
            fee_broker = gross_amount * 0.0015
            tax_ppn = fee_broker * 0.11
            fee_levy = gross_amount * 0.00043
            tax_pph = 0.0
            total_fee = fee_broker + tax_ppn + fee_levy
            net_amount = gross_amount + total_fee
        else:
            fee_broker = gross_amount * 0.0025
            tax_ppn = fee_broker * 0.11
            fee_levy = gross_amount * 0.00043
            tax_pph = gross_amount * 0.0010  # PPh Final 0.1% penjualan saham
            total_fee = fee_broker + tax_ppn + fee_levy + tax_pph
            net_amount = gross_amount - total_fee

        return {
            "gross_amount": round(gross_amount, 2),
            "fee_broker": round(fee_broker, 2),
            "tax_ppn": round(tax_ppn, 2),
            "fee_levy": round(fee_levy, 2),
            "tax_pph": round(tax_pph, 2),
            "total_fee": round(total_fee, 2),
            "net_amount": round(net_amount, 2)
        }

    def calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float,
        available_cash: float
    ) -> Dict[str, Any]:
        """Menghitung jumlah lot yang boleh dibeli berdasarkan toleransi risiko modal.
        
        Formula:
        Risk Amount = Modal * Max Risk % (misal 1.5% dari Rp 10 Juta = Rp 150.000)
        Risk per Share = Entry Price - Stop Loss Price
        Max Shares = Risk Amount / Risk per Share
        Lots = floor(Max Shares / 100)
        """
        entry = align_to_tick(entry_price)
        sl = align_to_tick(stop_loss)
        
        if entry <= sl or entry <= 0:
            return {"lots": 0, "shares": 0, "is_valid": False, "reason": "Invalid SL level"}

        risk_per_share = entry - sl
        max_risk_amount = self.capital * self.max_risk_pct

        # Jumlah lembar teoritis berdasarkan toleransi risiko
        theoretical_shares = max_risk_amount / risk_per_share
        
        # Konversi ke Satuan Lot (1 Lot = 100 Lembar)
        lots_by_risk = int(theoretical_shares // LOT_SIZE)

        # Batasan modal kas yang tersedia (tidak boleh melebihi kas)
        est_cost_per_lot = (entry * LOT_SIZE) * (1 + self.buy_fee_pct)
        lots_by_cash = int(available_cash // est_cost_per_lot) if est_cost_per_lot > 0 else 0

        # Batasan eksposur maksimal per saham (maksimal 35% dari modal keseluruhan)
        max_capital_per_stock = self.capital * 0.35
        lots_by_exposure = int(max_capital_per_stock // est_cost_per_lot) if est_cost_per_lot > 0 else 0

        final_lots = max(0, min(lots_by_risk, lots_by_cash, lots_by_exposure))
        final_shares = final_lots * LOT_SIZE
        gross_value = final_shares * entry
        fee_details = self.calculate_fees(gross_value, is_buy=True)

        is_valid = final_lots > 0 and fee_details["net_amount"] <= available_cash

        return {
            "lots": final_lots,
            "shares": final_shares,
            "entry_price": entry,
            "stop_loss": sl,
            "gross_value": gross_value,
            "total_cost": fee_details["net_amount"],
            "fee_buy": fee_details["total_fee"],
            "risk_amount_idr": round(final_shares * risk_per_share, 2),
            "risk_pct_of_capital": round((final_shares * risk_per_share) / self.capital, 4) if self.capital > 0 else 0.0,
            "is_valid": is_valid,
            "reason": "OK" if is_valid else "Position size 0 or exceeds available cash"
        }

    def validate_new_order(
        self,
        ticker: str,
        current_open_positions_count: int,
        daily_realized_loss: float,
        available_cash: float,
        entry_price: float,
        stop_loss: float
    ) -> Tuple[bool, str]:
        """Melakukan validasi keamanan komprehensif sebelum order dikirim."""
        # 1. Cek Circuit Breaker Rugi Harian
        max_loss_idr = self.capital * self.max_daily_loss_pct
        if abs(daily_realized_loss) >= max_loss_idr and daily_realized_loss < 0:
            return False, f"Daily Loss Circuit Breaker Active: Kerugian hari ini (Rp{abs(daily_realized_loss):,.0f}) mencapai batas {self.max_daily_loss_pct:.1%}."

        # 2. Cek Batasan Jumlah Posisi Terbuka
        if current_open_positions_count >= self.max_positions:
            return False, f"Max Open Positions Reached: Maksimal {self.max_positions} posisi terbuka aktif."

        # 3. Hitung Sizing
        sizing = self.calculate_position_size(entry_price, stop_loss, available_cash)
        if not sizing["is_valid"]:
            return False, f"Sizing Rejection: {sizing['reason']}"

        return True, "Order Approved by Risk Engine"
