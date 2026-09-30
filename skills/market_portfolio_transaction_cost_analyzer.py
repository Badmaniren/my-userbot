import json
import os
import uuid

from skills.db_storage import db_storage
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator


def start_new(config, db_storage=None, **kwargs):
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")
    
    tx_id = config.get("transaction_id")
    if not tx_id:
        tx_id = uuid.uuid4().hex
        
    amount = config.get("amount", 10000.0)
    fee_rate = config.get("fee_rate", 0.001)
    
    total_cost = amount * fee_rate
    
    tax_calc = kwargs.get("market_portfolio_tax_calculator")
    if tax_calc and hasattr(tax_calc, "calculate"):
        tax_calc.calculate(amount)

    return {
        "status": "success",
        "transaction_id": tx_id,
        "total_cost": total_cost,
        "calculated_spread": 0.05
    }


class MarketPortfolioTransactionCostAnalyzer:
    def analyze_costs(self, payload):
        volume = payload.get("volume", 0.0)
        price = payload.get("price", 0.0)
        slippage = payload.get("slippage_metrics", {}).get("slippage_cost", 10.0)
        tax = payload.get("tax_metrics", {}).get("tax_amount", 5.0)
        
        base_cost = (volume * price) * 0.001
        total_cost = base_cost + slippage + tax

        portfolio_id = payload.get("portfolio_id")
        ticker = payload.get("ticker")
        
        if portfolio_id and ticker:
            db_storage.save_audit_record(portfolio_id, {
                "analyzed_ticker": ticker,
                "total_cost": total_cost
            })

        return {
            "total_cost": total_cost,
            "base_cost": base_cost,
            "slippage": slippage,
            "tax": tax
        }

    def export_report(self, payload):
        filepath = payload.get("filepath")
        analysis = payload.get("analysis")
        portfolio_id = payload.get("portfolio_id")
        
        report_data = {
            "portfolio_id": portfolio_id,
            "analysis": analysis
        }
        
        if filepath:
            with open(filepath, "w") as f:
                json.dump(report_data, f)


market_portfolio_transaction_cost_analyzer = MarketPortfolioTransactionCostAnalyzer()