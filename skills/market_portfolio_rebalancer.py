import io
from skills.db_storage import db_storage
from skills.market_parser import market_parser


class MarketPortfolioRebalancer:
    def compute_rebalance_orders(self, portfolio, targets, threshold, min_trade):
        total_value = sum(portfolio.values())
        deviations = {}
        orders = []

        if total_value == 0:
            for asset in portfolio:
                deviations[asset] = 0.0
            return {"orders": orders, "deviations": deviations}

        for asset, current_val in portfolio.items():
            current_weight = current_val / total_value
            target_weight = targets.get(asset, 0.0)
            deviation = round(current_weight - target_weight, 6)
            deviations[asset] = deviation

            if abs(deviation) >= threshold:
                diff_value = deviation * total_value
                if abs(diff_value) >= min_trade:
                    if diff_value > 0:
                        orders.append({"asset": asset, "action": "SELL", "amount": abs(diff_value)})
                    else:
                        orders.append({"asset": asset, "action": "BUY", "amount": abs(diff_value)})

        return {"orders": orders, "deviations": deviations}

    def fetch_and_rebalance(self, portfolio_id):
        targets = db_storage("get_target_weights", portfolio_id)
        portfolio = {}
        if isinstance(targets, dict):
            for asset, weight in targets.items():
                portfolio[asset] = 1000.0
        return self.compute_rebalance_orders(portfolio, targets if isinstance(targets, dict) else {}, 0.01, 10.0)

    def process_market_stream(self, stream_data):
        return market_parser.parse_stream(stream_data)


def market_portfolio_rebalancer(config):
    portfolio_id = config.get("portfolio_id")
    portfolio_state = db_storage("get_portfolio", portfolio_id)
    if not portfolio_state:
        portfolio_state = {
            "assets": {
                config.get("market_data", {}).get("symbol", "TEST"): {
                    "quantity": 10,
                    "target_weight": 0.5
                }
            },
            "trigger_threshold": 0.01,
            "min_order_value": 10.0
        }

    assets = portfolio_state.get("assets", {})
    market_data = config.get("market_data", {})
    symbol = market_data.get("symbol")
    price = market_data.get("price", 100.0)

    portfolio = {}
    targets = {}

    for sym, data in assets.items():
        qty = data.get("quantity", 0)
        p = price if sym == symbol else 100.0
        portfolio[sym] = qty * p
        targets[sym] = data.get("target_weight", 0.0)

    rebalancer = MarketPortfolioRebalancer()
    result = rebalancer.compute_rebalance_orders(
        portfolio=portfolio,
        targets=targets,
        threshold=portfolio_state.get("trigger_threshold", 0.01),
        min_trade=portfolio_state.get("min_order_value", 10.0)
    )

    db_storage("save_orders", (portfolio_id, result.get("orders")))
    return result
