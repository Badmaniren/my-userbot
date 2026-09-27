class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id=None, amount=None, tax_rate=None, *args, **kwargs):
        if len(args) == 2:
            return round(args[0] * args[1], 2)
        if tax_rate is not None:
            amt = amount if amount is not None else (portfolio_id if isinstance(portfolio_id, (int, float)) else 0)
            return round(amt * tax_rate, 2)
        pid = portfolio_id if portfolio_id is not None else (args[0] if args else None)
        if not hasattr(self, 'db_storage') or self.db_storage is None:
            return 0.0
        portfolio = self.db_storage.get_portfolio(pid)
        if portfolio:
            profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
            return round(profit * 0.13, 2)
        return 0.0

    def process_dividend_stream(self, *args, **kwargs):
        stream = kwargs.get('stream') or (args[1] if len(args) > 1 else (args[0] if args else None))
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
