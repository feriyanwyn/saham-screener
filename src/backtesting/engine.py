"""Walk-Forward Backtesting Engine for Indonesian Stock Market (IDX).
Menguji strategi kuantitatif secara realistis pada data historis intraday
tanpa look-ahead bias, memperhitungkan friksi komisi bursa, pajak, dan slippage.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from config.idx_constants import LOT_SIZE, align_to_tick, get_tick_size
from config.settings import settings
from src.risk_management.risk_manager import RiskManager
from src.technical_analysis.indicators import TechnicalAnalysisEngine


class BacktestEngine:
    """Quantitative event-driven backtesting engine for IDX scalping strategies."""

    def __init__(
        self,
        initial_capital: float = 10_000_000.0,
        slippage_ticks: int = 1,
        buy_fee_pct: float = settings.BROKER_BUY_FEE_PCT,
        sell_fee_pct: float = settings.BROKER_SELL_FEE_PCT
    ):
        self.initial_capital = initial_capital
        self.slippage_ticks = slippage_ticks
        self.risk_manager = RiskManager(
            capital=initial_capital,
            buy_fee_pct=buy_fee_pct,
            sell_fee_pct=sell_fee_pct
        )

    def run_backtest(
        self,
        df_candles: pd.DataFrame,
        ticker: str,
        strategy_name: str = "Scalping_V1"
    ) -> Dict[str, Any]:
        """Menjalankan backtest walk-forward candle demi candle."""
        if df_candles.empty or len(df_candles) < 30:
            return {"error": "Insufficient historical candles for backtesting"}

        df_ta = TechnicalAnalysisEngine.apply_all_indicators(df_candles)
        
        capital = self.initial_capital
        cash = capital
        position: Optional[Dict[str, Any]] = None
        trade_logs: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        peak_equity = capital
        max_drawdown_idr = 0.0
        max_drawdown_pct = 0.0

        for i in range(25, len(df_ta) - 1):
            curr_candle = df_ta.iloc[i]
            next_candle = df_ta.iloc[i + 1]
            timestamp = str(curr_candle["timestamp"]) if "timestamp" in df_ta.columns else str(curr_candle.name)

            # 1. Update Portfolio Valuation
            current_close = float(curr_candle["close"])
            if position:
                unrealized_pnl = (current_close - position["entry_price"]) * position["shares"]
                current_equity = cash + (position["shares"] * current_close)
            else:
                current_equity = cash

            if current_equity > peak_equity:
                peak_equity = current_equity
            dd = peak_equity - current_equity
            dd_pct = (dd / peak_equity) if peak_equity > 0 else 0.0
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct
                max_drawdown_idr = dd

            equity_curve.append({
                "timestamp": timestamp,
                "equity": round(current_equity, 2),
                "cash": round(cash, 2),
                "drawdown_pct": round(dd_pct * 100, 2)
            })

            # 2. Jika Sedang Memegang Posisi: Cek Kondisi Exit (TP / SL / Time stop)
            if position:
                exit_triggered = False
                exit_reason = ""
                raw_exit_price = current_close

                # Cek Stop Loss
                if curr_candle["low"] <= position["stop_loss"]:
                    exit_triggered = True
                    exit_reason = "STOP_LOSS"
                    raw_exit_price = min(position["stop_loss"], curr_candle["open"])

                # Cek Take Profit
                elif curr_candle["high"] >= position["take_profit"]:
                    exit_triggered = True
                    exit_reason = "TAKE_PROFIT"
                    raw_exit_price = max(position["take_profit"], curr_candle["open"])

                # Cek Sinyal Bearish Exit
                elif curr_candle["rsi_14"] >= 75.0 or curr_candle["macd_bearish_cross"]:
                    exit_triggered = True
                    exit_reason = "TECHNICAL_EXIT"
                    raw_exit_price = float(next_candle["open"])

                if exit_triggered:
                    # Terapkan slippage
                    tick = get_tick_size(raw_exit_price)
                    exec_exit_price = align_to_tick(raw_exit_price - (self.slippage_ticks * tick))
                    gross_sell = position["shares"] * exec_exit_price
                    fee_sell = self.risk_manager.calculate_fees(gross_sell, is_buy=False)

                    net_proceeds = fee_sell["net_amount"]
                    cash += net_proceeds
                    trade_pnl = net_proceeds - position["total_cost"]
                    trade_pnl_pct = trade_pnl / position["total_cost"]

                    trade_logs.append({
                        "ticker": ticker,
                        "entry_time": position["entry_time"],
                        "exit_time": timestamp,
                        "lots": position["lots"],
                        "entry_price": position["entry_price"],
                        "exit_price": exec_exit_price,
                        "exit_reason": exit_reason,
                        "gross_pnl": (exec_exit_price - position["entry_price"]) * position["shares"],
                        "net_pnl": round(trade_pnl, 2),
                        "pnl_pct": round(trade_pnl_pct * 100, 2),
                        "total_fees": round(position["fee_buy"] + fee_sell["total_fee"], 2)
                    })
                    position = None
                continue

            # 3. Jika Tidak Memegang Posisi: Evaluasi Sinyal Entry untuk Candle Berikutnya
            rsi = curr_candle["rsi_14"]
            rel_vol = curr_candle["relative_volume"]
            above_vwap = curr_candle["above_vwap"]

            # Logika Signal Sederhana & Kuat
            buy_signal = (
                (42.0 <= rsi <= 65.0) and
                above_vwap and
                (curr_candle["macd_bullish_cross"] or curr_candle["macd"] > curr_candle["macd_signal"]) and
                rel_vol >= 1.2
            )

            if buy_signal and not position:
                # Eksekusi terjadi pada pembukaan candle berikutnya (zero lookahead)
                raw_entry = float(next_candle["open"])
                tick = get_tick_size(raw_entry)
                entry_exec = align_to_tick(raw_entry + (self.slippage_ticks * tick))

                atr = float(curr_candle.get("atr_14", tick * 3))
                sl = align_to_tick(entry_exec - (1.5 * atr))
                tp = align_to_tick(entry_exec + (2.5 * atr))

                sizing = self.risk_manager.calculate_position_size(entry_exec, sl, cash)
                if sizing["is_valid"] and sizing["lots"] > 0:
                    cash -= sizing["total_cost"]
                    entry_ts = str(next_candle["timestamp"]) if "timestamp" in df_ta.columns else str(next_candle.name)
                    position = {
                        "entry_time": entry_ts,
                        "lots": sizing["lots"],
                        "shares": sizing["shares"],
                        "entry_price": entry_exec,
                        "stop_loss": sl,
                        "take_profit": tp,
                        "total_cost": sizing["total_cost"],
                        "fee_buy": sizing["fee_buy"]
                    }

        # 4. Rekapitulasi Statistik Kinerja
        total_trades = len(trade_logs)
        if total_trades == 0:
            return {
                "strategy_name": strategy_name,
                "total_trades": 0,
                "win_rate": 0.0,
                "net_profit": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": round(max_drawdown_pct * 100, 2),
                "trades": [],
                "equity_curve": equity_curve
            }

        winning_trades = [t for t in trade_logs if t["net_pnl"] > 0]
        losing_trades = [t for t in trade_logs if t["net_pnl"] <= 0]

        win_rate = (len(winning_trades) / total_trades) * 100.0
        gross_profit = sum(t["net_pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["net_pnl"] for t in losing_trades))
        net_profit = sum(t["net_pnl"] for t in trade_logs)
        net_profit_pct = (net_profit / self.initial_capital) * 100.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        avg_win = gross_profit / len(winning_trades) if winning_trades else 0.0
        avg_loss = gross_loss / len(losing_trades) if losing_trades else 0.0
        expectancy = ((win_rate / 100.0) * avg_win) - (((100.0 - win_rate) / 100.0) * avg_loss)

        # Sharpe Ratio sederhana
        pnl_series = pd.Series([t["pnl_pct"] for t in trade_logs])
        sharpe = round((pnl_series.mean() / pnl_series.std()) * np.sqrt(total_trades), 2) if pnl_series.std() > 0 else 0.0

        return {
            "strategy_name": strategy_name,
            "ticker": ticker,
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_curve[-1]["equity"] if equity_curve else self.initial_capital, 2),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "net_profit": round(net_profit, 2),
            "net_profit_pct": round(net_profit_pct, 2),
            "profit_factor": profit_factor,
            "max_drawdown_idr": round(max_drawdown_idr, 2),
            "max_drawdown_pct": round(max_drawdown_pct * 100, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "sharpe_ratio": sharpe,
            "trades": trade_logs,
            "equity_curve": equity_curve
        }
