import io
import os
import json

from skills.db_storage import db_storage
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer


def calculate_capital_gains(asset_data: dict) -> float:
    shares = asset_data.get("shares", 0)
    purchase_price = asset_data.get("purchase_price", 0.0)
    current_price = asset_data.get("current_price", 0.0)
    total_cost = shares * purchase_price
    current_value = shares * current_price
    return float(current_value - total_cost)


def evaluate_portfolio_tax_liability(portfolio_id: str, tax_rate: float) -> dict:
    stream = db_storage.fetch_stream(portfolio_id)
    total_gain = 0.0

    if stream:
        content = stream.read()
        if content:
            lines = content.decode('utf-8').splitlines()
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(',')
                data = {}
                for part in parts:
                    if ':' in part:
                        k, v = part.split(':', 1)
                        data[k.strip()] = v.strip()
                if "gain" in data:
                    try:
                        total_gain += float(data["gain"])
                    except ValueError:
                        pass

    tax_liability = max(0.0, total_gain * tax_rate)
    return {
        "portfolio_id": portfolio_id,
        "tax_liability": tax_liability
    }


def optimize_tax_rebalance(portfolio_id: str, portfolio_config: dict) -> dict:
    market_portfolio_strategy_optimizer.calculate_target_weights(portfolio_config)

    assets = portfolio_config.get("assets", [])
    tax_rate = portfolio_config.get("tax_rate", 0.15)

    total_gain = 0.0
    for asset in assets:
        total_gain += calculate_capital_gains(asset)

    estimated_tax = max(0.0, total_gain * tax_rate)

    recommended_actions = []
    for asset in assets:
        recommended_actions.append({
            "ticker": asset.get("ticker"),
            "action": "HOLD"
        })

    return {
        "portfolio_id": portfolio_id,
        "recommended_actions": recommended_actions,
        "estimated_tax_impact": estimated_tax
    }


class MarketPortfolioTaxRebalanceOptimizerClass:
    def optimize(self, portfolio_id: str, target_allocations: dict, tax_bracket: float) -> dict:
        valuation = market_portfolio_valuation.calculate_value(portfolio_id)

        total_gain = 0.0
        for ticker in target_allocations.keys():
            gain_res = market_portfolio_tax_calculator.evaluate_capital_gains(
                portfolio_id=portfolio_id,
                ticker=ticker,
                current_price=100.0
            )
            if isinstance(gain_res, (int, float)):
                total_gain += float(gain_res)
            elif isinstance(gain_res, dict):
                total_gain += float(gain_res.get("gain", 0.0))

        estimated_tax = max(0.0, total_gain * tax_bracket)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/rebalance_{portfolio_id}.json"
        report_data = {
            "portfolio_id": portfolio_id,
            "target_allocations": target_allocations,
            "estimated_tax": estimated_tax,
            "valuation": valuation
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f)

        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "estimated_tax_impact": estimated_tax
        }


market_portfolio_tax_rebalance_optimizer = MarketPortfolioTaxRebalanceOptimizerClass()