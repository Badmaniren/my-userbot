import os
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Union

from skills.db_storage import db_storage
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core


@dataclass
class RebalanceOrder:
    ticker: str
    side: str
    quantity: float
    amount: float = 0.0
    symbol: str = ""
    action: str = ""

    def __post_init__(self):
        if not self.symbol:
            self.symbol = self.ticker
        if not self.action:
            self.action = self.side


@dataclass
class RebalancePlan:
    orders: List[RebalanceOrder] = field(default_factory=list)
    drift_detected: bool = False


class PortfolioRebalancePlanner:
    def __init__(
        self,
        drift_threshold: float = 0.01,
        cash_buffer_pct: float = 0.0,
        allow_fractional: bool = True,
        min_trade_value: float = 0.0,
    ):
        self.drift_threshold = drift_threshold
        self.cash_buffer_pct = cash_buffer_pct
        self.allow_fractional = allow_fractional
        self.min_trade_value = min_trade_value

    def calculate_drifts(
        self,
        positions: Dict[str, Dict[str, float]],
        target_weights: Dict[str, float],
        cash: float,
    ) -> Dict[str, float]:
        if cash < 0:
            raise ValueError("Cash cannot be negative")

        portfolio_values = {}
        total_assets_val = 0.0

        for ticker, pos in positions.items():
            qty = pos.get("quantity", 0.0)
            price = pos.get("price", 0.0)
            if price < 0:
                raise ValueError("Price cannot be negative")
            val = qty * price
            portfolio_values[ticker] = val
            total_assets_val += val

        total_val = total_assets_val + cash
        if total_val <= 0:
            total_val = 1.0

        current_weights = {}
        for ticker, val in portfolio_values.items():
            current_weights[ticker] = val / total_val

        all_tickers = set(current_weights.keys()).union(set(target_weights.keys()))
        drifts = {}
        for ticker in all_tickers:
            cw = current_weights.get(ticker, 0.0)
            tw = target_weights.get(ticker, 0.0)
            if tw > 1.0 or tw < 0.0:
                raise ValueError("Target weight out of bounds")
            drifts[ticker] = cw - tw

        return drifts

    def plan_rebalance(
        self,
        positions: Dict[str, Dict[str, float]],
        target_weights: Dict[str, float],
        cash: float,
    ) -> RebalancePlan:
        if cash < 0:
            raise ValueError("Cash cannot be negative")

        for ticker, pos in positions.items():
            if pos.get("price", 0.0) < 0:
                raise ValueError("Price cannot be negative")

        for tw in target_weights.values():
            if tw > 1.0 or tw < 0.0:
                raise ValueError("Target weight out of bounds")

        drifts = self.calculate_drifts(positions, target_weights, cash)

        portfolio_values = {}
        total_assets_val = 0.0
        for ticker, pos in positions.items():
            qty = pos.get("quantity", 0.0)
            price = pos.get("price", 0.0)
            val = qty * price
            portfolio_values[ticker] = val
            total_assets_val += val

        total_val = total_assets_val + cash

        if self.cash_buffer_pct > 0:
            reserved_cash = cash * self.cash_buffer_pct
            spendable_cash = cash - reserved_cash
        else:
            spendable_cash = float("inf")

        sells = []
        buys = []
        drift_detected = False

        for ticker, drift in drifts.items():
            if abs(drift) >= self.drift_threshold:
                drift_detected = True

            if abs(drift) < self.drift_threshold:
                continue

            target_w = target_weights.get(ticker, 0.0)
            target_val = total_val * target_w
            current_val = portfolio_values.get(ticker, 0.0)
            diff_val = target_val - current_val

            if abs(diff_val) < self.min_trade_value:
                continue

            price = positions.get(ticker, {}).get("price", 0.0)
            if price <= 0:
                continue

            if diff_val < 0:
                # Sell
                qty_diff = abs(diff_val) / price
                current_qty = positions.get(ticker, {}).get("quantity", 0.0)
                if qty_diff > current_qty:
                    qty_diff = current_qty

                if not self.allow_fractional:
                    qty_diff = math.floor(qty_diff)

                if qty_diff > 0:
                    trade_val = qty_diff * price
                    if self.cash_buffer_pct > 0:
                        spendable_cash += trade_val
                    sells.append(
                        RebalanceOrder(
                            ticker=ticker,
                            side="SELL",
                            quantity=qty_diff,
                            amount=trade_val,
                            symbol=ticker,
                            action="SELL"
                        )
                    )
            elif diff_val > 0:
                # Buy
                qty_diff = diff_val / price
                if not self.allow_fractional:
                    qty_diff = math.floor(qty_diff)

                trade_val = qty_diff * price
                if trade_val > spendable_cash:
                    trade_val = max(0.0, spendable_cash)
                    qty_diff = trade_val / price
                    if not self.allow_fractional:
                        qty_diff = math.floor(qty_diff)
                    trade_val = qty_diff * price

                if qty_diff > 0 and trade_val <= spendable_cash + 1e-4:
                    if self.cash_buffer_pct > 0:
                        spendable_cash -= trade_val
                    buys.append(
                        RebalanceOrder(
                            ticker=ticker,
                            side="BUY",
                            quantity=qty_diff,
                            amount=trade_val,
                            symbol=ticker,
                            action="BUY"
                        )
                    )

        orders = sells + buys
        return RebalancePlan(orders=orders, drift_detected=drift_detected)


def market_portfolio_rebalance_planner(portfolio_id: str, liquidity_buffer: float = 0.0) -> Dict[str, Any]:
    state = db_storage.load_portfolio_state(portfolio_id)
    if not state:
        return {"orders": [], "drift_detected": False}

    assets = state.get("assets", {})
    cash = state.get("cash", 0.0)

    positions = {}
    target_weights = {}

    for ticker, data in assets.items():
        positions[ticker] = {
            "quantity": data.get("quantity", 0.0),
            "price": data.get("price", 0.0),
        }
        target_weights[ticker] = data.get("target_weight", 0.0)

    total_assets_val = sum(p["quantity"] * p["price"] for p in positions.values())
    total_val = total_assets_val + cash

    cash_buffer_pct = (liquidity_buffer / total_val) if total_val > 0 else 0.0

    planner = PortfolioRebalancePlanner(
        drift_threshold=0.01,
        cash_buffer_pct=cash_buffer_pct,
        allow_fractional=True
    )

    plan = planner.plan_rebalance(positions, target_weights, cash)

    orders_list = []
    for o in plan.orders:
        orders_list.append({
            "symbol": o.symbol,
            "action": o.action,
            "quantity": o.quantity,
            "amount": o.amount
        })

    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/rebalance_{portfolio_id}.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Rebalanced portfolio {portfolio_id} with {len(orders_list)} orders.")

    return {
        "orders": orders_list,
        "drift_detected": plan.drift_detected
    }