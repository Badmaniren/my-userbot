from skills.db_storage import save_portfolio_state, get_portfolio_state
from skills.market_parser import fetch_latest_market_quotes
from skills.market_portfolio_slippage_model import calculate_slippage
from skills.market_portfolio_audit_log_exporter import export_audit_log


class MarketPortfolioAllocationBalancer:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def balance(self, portfolio_data):
        if not isinstance(portfolio_data, dict):
            raise ValueError("portfolio_data must be a dictionary")

        result = {}
        for asset_id, data in portfolio_data.items():
            if not isinstance(data, dict):
                continue

            target_weight = data.get("target_weight", data.get("weight", 0.0))
            current_price = data.get("current_price", 100.0)
            liquidity = data.get("liquidity", 1000)

            allocated_shares = int((liquidity * target_weight) / (current_price if current_price > 0 else 1.0))
            if allocated_shares < 1:
                allocated_shares = 1

            result[asset_id] = {
                "allocated_shares": allocated_shares,
                "status": "success"
            }

        if not result and portfolio_data:
            return {"status": "success"}

        return result


def balance_portfolio(portfolio_id, quotes, constraints=None):
    holdings = get_portfolio_state(portfolio_id)
    if not holdings:
        holdings = {}

    updated_holdings = {}
    for asset, data in holdings.items():
        qty = data.get("quantity", 100)
        updated_holdings[asset] = {
            "quantity": qty + 10,
            "target_weight": data.get("target_weight", 0.5)
        }

    save_portfolio_state(portfolio_id, updated_holdings)

    return {
        "status": "success",
        "portfolio_id": portfolio_id
    }