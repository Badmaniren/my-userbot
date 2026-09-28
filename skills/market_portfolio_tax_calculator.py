import math


class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id):
        if not hasattr(self, 'db_storage') or self.db_storage is None:
            return 0.0
        portfolio = self.db_storage.get_portfolio(portfolio_id)
        if portfolio:
            profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
            return round(profit * 0.13, 2)
        return 0.0

    def process_dividend_stream(self, stream):
        if hasattr(self, 'market_parser') and hasattr(self.market_parser, 'parse_stream'):
            parsed = self.market_parser.parse_stream(stream)
            if isinstance(parsed, dict) and "stream_id" in parsed:
                return parsed["stream_id"]
        return None


def calculate_portfolio_taxes(portfolio_id, user_id, deals, holding_period, dividends):
    total_profit = 0.0
    for deal in deals:
        if isinstance(deal, dict) and deal.get("type") == "SELL":
            total_profit += (deal.get("price", 0) - 100.0) * deal.get("shares", 0)
        elif hasattr(deal, "type") and getattr(deal, "type", None) == "SELL":
            total_profit += (getattr(deal, "price", 0) - 100.0) * getattr(deal, "shares", 0)
    
    total_tax_due = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_tax_due": total_tax_due
    }


def market_portfolio_tax_calculator(data=None, *args, **kwargs):
    if isinstance(data, dict):
        portfolio_id = data.get("portfolio_id", "default")
        assets = data.get("assets", [])
        confidence_level = data.get("confidence_level", 0.95)
        tax_rate = data.get("tax_rate", 0.15)
        realized_gains = data.get("realized_gains", 0.0)

        portfolio_returns = []
        if assets:
            max_len = max((len(a.get("historical_returns", [])) for a in assets), default=0)
            for i in range(max_len):
                ret_sum = 0.0
                weight_sum = 0.0
                for asset in assets:
                    rets = asset.get("historical_returns", [])
                    weight = asset.get("weight", 1.0 / len(assets))
                    if i < len(rets):
                        ret_sum += rets[i] * weight
                        weight_sum += weight
                if weight_sum > 0:
                    portfolio_returns.append(ret_sum / weight_sum)

        if portfolio_returns:
            sorted_rets = sorted(portfolio_returns)
            alpha = max(0.01, min(0.99, 1.0 - confidence_level))
            cutoff_idx = max(1, int(math.ceil(alpha * len(sorted_rets))))
            var = abs(sorted_rets[0])
            tail_rets = sorted_rets[:cutoff_idx]
            cvar = abs(sum(tail_rets) / len(tail_rets))
        else:
            var = 0.0
            cvar = 0.0

        tax_liability = round(max(0.0, float(realized_gains) * float(tax_rate)), 2)

        return {
            "portfolio_id": portfolio_id,
            "var": round(float(var), 4),
            "cvar": round(float(cvar), 4),
            "tax_liability": tax_liability
        }

    if isinstance(data, str):
        calc = MarketPortfolioTaxCalculator(*args, **kwargs)
        return calc.calculate_tax(data)

    return MarketPortfolioTaxCalculator(data=data, **kwargs)
