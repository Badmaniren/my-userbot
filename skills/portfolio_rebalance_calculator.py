import sys
import datetime
import uuid
import requests

from skills.db_storage import DatabaseStorage
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class PortfolioRebalanceCalculator:
    def compute_orders(self, portfolio_state):
        orders = []
        assets = portfolio_state.get("assets", {})
        cash = portfolio_state.get("cash", 0.0)
        total_value = portfolio_state.get("total_value", 0.0)
        drift_threshold = portfolio_state.get("drift_threshold", 0.05)

        for asset_id, data in assets.items():
            current_weight = data.get("current_weight", 0.0)
            target_weight = data.get("target_weight", 0.0)
            price = data.get("price", 1.0)

            diff = target_weight - current_weight
            if abs(diff) <= drift_threshold:
                continue

            if diff > 0:
                action = "BUY"
                ideal_qty = int((diff * total_value) / price)
                max_affordable_qty = int(cash // price)
                quantity = min(ideal_qty, max_affordable_qty)
            else:
                action = "SELL"
                quantity = int(((-diff) * total_value) / price)

            if quantity > 0:
                orders.append({
                    "asset_id": asset_id,
                    "action": action,
                    "quantity": quantity
                })

        return orders

def calculate_portfolio_rebalance(portfolio_id, drift_threshold=0.05):
    db = DatabaseStorage()
    portfolio_state = db.get_portfolio_state(portfolio_id) or {}

    cash = portfolio_state.get("cash", 0.0)
    assets_raw = portfolio_state.get("assets", {})

    parser = MarketParser()
    symbols = list(assets_raw.keys())
    prices = parser.fetch_latest_prices(symbols)

    valuation = PortfolioValuation()
    total_value = valuation.calculate_total_value(portfolio_id)
    if total_value == 0:
        total_value = cash + sum(data.get("shares", 0) * prices.get(sym, 0.0) for sym, data in assets_raw.items())
        if total_value == 0:
            total_value = 1.0

    assets_formatted = {}
    for sym, data in assets_raw.items():
        shares = data.get("shares", 0)
        price = prices.get(sym, 1.0)
        asset_val = shares * price
        current_weight = asset_val / total_value if total_value > 0 else 0.0
        assets_formatted[sym] = {
            "name": sym,
            "current_weight": current_weight,
            "target_weight": data.get("target_weight", 0.0),
            "price": price
        }

    state_for_calc = {
        "assets": assets_formatted,
        "cash": cash,
        "total_value": total_value,
        "drift_threshold": drift_threshold
    }

    calculator = PortfolioRebalanceCalculator()
    orders = calculator.compute_orders(state_for_calc)

    db.save_rebalance_orders(portfolio_id, orders)

    return {
        "portfolio_id": portfolio_id,
        "status": "success",
        "orders": orders
    }