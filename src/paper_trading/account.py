"""Paper Trading Account & Execution Simulator for IDX Stocks.
Mengelola simulasi saldo virtual, eksekusi beli/jual dengan potongan biaya resmi BEI,
pemantauan open positions, dan pencatatan realized/unrealized P&L.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from config.idx_constants import LOT_SIZE, align_to_tick, get_tick_size
from config.settings import settings
from database.connection import SessionLocal
from database.models import PaperAccount, PaperPosition, PaperOrder
from src.risk_management.risk_manager import RiskManager


class PaperTradingSimulator:
    """Virtual portfolio and execution engine with realistic IDX microstructure modeling."""

    def __init__(
        self, 
        account_id: str = "MAIN_PAPER_ACCOUNT", 
        initial_balance: float = settings.INITIAL_CAPITAL_IDR,
        db_session: Optional[Session] = None
    ):
        self.account_id = account_id
        self.initial_balance = initial_balance
        self.db = db_session or SessionLocal()
        self.risk_manager = RiskManager(capital=initial_balance)
        self._ensure_account_exists()

    def _ensure_account_exists(self):
        """Memastikan akun simulasi terdaftar di DB."""
        acc = self.db.query(PaperAccount).filter(PaperAccount.account_id == self.account_id).first()
        if not acc:
            acc = PaperAccount(
                account_id=self.account_id,
                initial_balance=self.initial_balance,
                current_cash=self.initial_balance,
                total_equity=self.initial_balance
            )
            self.db.add(acc)
            self.db.commit()

    def get_account(self) -> PaperAccount:
        return self.db.query(PaperAccount).filter(PaperAccount.account_id == self.account_id).first()

    def execute_buy(
        self,
        ticker: str,
        price: float,
        lots: int,
        stop_loss: float,
        take_profit: float,
        signal_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Mengeksekusi order pembelian saham virtual."""
        acc = self.get_account()
        exec_price = align_to_tick(price)
        sl = align_to_tick(stop_loss)
        tp = align_to_tick(take_profit)
        shares = lots * LOT_SIZE
        gross_value = shares * exec_price

        fee_info = self.risk_manager.calculate_fees(gross_value, is_buy=True)
        total_cost = fee_info["net_amount"]

        if lots <= 0:
            return {"status": "REJECTED", "reason": "Lot quantity must be greater than 0"}

        if total_cost > acc.current_cash:
            return {
                "status": "REJECTED", 
                "reason": f"Insufficient cash: Required Rp{total_cost:,.0f}, Available Rp{acc.current_cash:,.0f}"
            }

        # 1. Update Saldo Kas
        acc.current_cash -= total_cost
        acc.updated_at = datetime.utcnow()

        # 2. Catat Order
        order_id = f"ORD-B-{uuid.uuid4().hex[:8].upper()}"
        order = PaperOrder(
            order_id=order_id,
            account_id=self.account_id,
            signal_id=signal_id,
            ticker=ticker.upper(),
            order_type="BUY",
            order_price=exec_price,
            lot_quantity=lots,
            gross_amount=gross_value,
            fee_broker=fee_info["fee_broker"],
            fee_levy=fee_info["fee_levy"],
            tax_pph=fee_info["tax_pph"],
            tax_ppn=fee_info["tax_ppn"],
            net_amount=total_cost,
            execution_status="FILLED"
        )
        self.db.add(order)

        # 3. Update atau Buka Posisi Baru
        pos = (
            self.db.query(PaperPosition)
            .filter(PaperPosition.account_id == self.account_id, PaperPosition.ticker == ticker.upper())
            .first()
        )
        if pos:
            # Average down / up
            total_shares = (pos.lot_quantity * LOT_SIZE) + shares
            new_avg = ((pos.average_entry_price * pos.lot_quantity * LOT_SIZE) + gross_value) / total_shares
            pos.lot_quantity += lots
            pos.average_entry_price = round(new_avg, 2)
            pos.current_price = exec_price
            pos.stop_loss = sl
            pos.take_profit = tp
            pos.updated_at = datetime.utcnow()
        else:
            pos = PaperPosition(
                account_id=self.account_id,
                ticker=ticker.upper(),
                lot_quantity=lots,
                average_entry_price=exec_price,
                current_price=exec_price,
                stop_loss=sl,
                take_profit=tp,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0
            )
            self.db.add(pos)

        self.db.commit()
        return {
            "status": "FILLED",
            "order_id": order_id,
            "ticker": ticker.upper(),
            "lots": lots,
            "price": exec_price,
            "total_cost": total_cost,
            "remaining_cash": acc.current_cash
        }

    def execute_sell(
        self,
        ticker: str,
        price: float,
        lots: Optional[int] = None,
        signal_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Mengeksekusi order penjualan saham virtual (Take Profit / Stop Loss / Manual)."""
        acc = self.get_account()
        pos = (
            self.db.query(PaperPosition)
            .filter(PaperPosition.account_id == self.account_id, PaperPosition.ticker == ticker.upper())
            .first()
        )

        if not pos or pos.lot_quantity <= 0:
            return {"status": "REJECTED", "reason": f"No open position found for {ticker.upper()}"}

        sell_lots = pos.lot_quantity if lots is None else min(pos.lot_quantity, lots)
        exec_price = align_to_tick(price)
        shares = sell_lots * LOT_SIZE
        gross_value = shares * exec_price

        fee_info = self.risk_manager.calculate_fees(gross_value, is_buy=False)
        net_proceeds = fee_info["net_amount"]

        # Hitung Realized P&L
        cost_basis = shares * pos.average_entry_price
        realized_pnl = net_proceeds - cost_basis
        realized_pnl_pct = realized_pnl / cost_basis if cost_basis > 0 else 0.0

        # 1. Update Saldo Kas
        acc.current_cash += net_proceeds
        acc.updated_at = datetime.utcnow()

        # 2. Catat Order Penjualan
        order_id = f"ORD-S-{uuid.uuid4().hex[:8].upper()}"
        order = PaperOrder(
            order_id=order_id,
            account_id=self.account_id,
            signal_id=signal_id,
            ticker=ticker.upper(),
            order_type="SELL",
            order_price=exec_price,
            lot_quantity=sell_lots,
            gross_amount=gross_value,
            fee_broker=fee_info["fee_broker"],
            fee_levy=fee_info["fee_levy"],
            tax_pph=fee_info["tax_pph"],
            tax_ppn=fee_info["tax_ppn"],
            net_amount=net_proceeds,
            execution_status="FILLED"
        )
        self.db.add(order)

        # 3. Update Posisi
        pos.lot_quantity -= sell_lots
        if pos.lot_quantity <= 0:
            self.db.delete(pos)
        else:
            pos.current_price = exec_price
            pos.updated_at = datetime.utcnow()

        self.db.commit()
        return {
            "status": "FILLED",
            "order_id": order_id,
            "ticker": ticker.upper(),
            "lots_sold": sell_lots,
            "price": exec_price,
            "net_proceeds": net_proceeds,
            "realized_pnl": round(realized_pnl, 2),
            "realized_pnl_pct": round(realized_pnl_pct * 100, 2),
            "remaining_cash": acc.current_cash
        }

    def get_portfolio_summary(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Mengambil rangkuman nilai portofolio terkini, posisi terbuka, dan P&L."""
        acc = self.get_account()
        positions = (
            self.db.query(PaperPosition)
            .filter(PaperPosition.account_id == self.account_id)
            .all()
        )

        prices = current_prices or {}
        total_market_value = 0.0
        total_unrealized_pnl = 0.0
        pos_list = []

        for p in positions:
            curr_p = prices.get(p.ticker, p.current_price)
            shares = p.lot_quantity * LOT_SIZE
            val = shares * curr_p
            cost = shares * p.average_entry_price
            unreal_pnl = val - cost
            unreal_pnl_pct = (unreal_pnl / cost) * 100 if cost > 0 else 0.0

            total_market_value += val
            total_unrealized_pnl += unreal_pnl

            pos_list.append({
                "ticker": p.ticker,
                "lots": p.lot_quantity,
                "shares": shares,
                "avg_price": p.average_entry_price,
                "current_price": curr_p,
                "market_value": round(val, 2),
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "unrealized_pnl": round(unreal_pnl, 2),
                "unrealized_pnl_pct": round(unreal_pnl_pct, 2)
            })

        total_equity = acc.current_cash + total_market_value
        acc.total_equity = total_equity
        self.db.commit()

        # Riwayat realized P&L dari order jual
        sell_orders = (
            self.db.query(PaperOrder)
            .filter(PaperOrder.account_id == self.account_id, PaperOrder.order_type == "SELL")
            .all()
        )

        return {
            "account_id": self.account_id,
            "initial_balance": acc.initial_balance,
            "cash": round(acc.current_cash, 2),
            "equity": round(total_equity, 2),
            "market_value": round(total_market_value, 2),
            "unrealized_pnl": round(total_unrealized_pnl, 2),
            "unrealized_pnl_pct": round((total_unrealized_pnl / acc.initial_balance) * 100, 2) if acc.initial_balance > 0 else 0.0,
            "open_positions": pos_list,
            "total_open_positions": len(pos_list),
            "total_closed_trades": len(sell_orders)
        }

    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Mengambil daftar riwayat transaksi order virtual."""
        orders = (
            self.db.query(PaperOrder)
            .filter(PaperOrder.account_id == self.account_id)
            .order_by(PaperOrder.executed_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "order_id": o.order_id,
                "time": o.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": o.ticker,
                "type": o.order_type,
                "price": o.order_price,
                "lots": o.lot_quantity,
                "gross_amount": o.gross_amount,
                "fees": round(o.fee_broker + o.fee_levy + o.tax_pph + o.tax_ppn, 2),
                "net_amount": o.net_amount,
                "status": o.execution_status
            }
            for o in orders
        ]
