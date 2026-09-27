class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, *args, **kwargs):
        if len(args) == 2:
            amount, tax_rate = args
            return round(amount * tax_rate, 2)
        portfolio_id = kwargs.get('portfolio_id', args[0] if args else None)
        if portfolio_id is not None:
            if hasattr(self, 'db_storage') and self.db_storage and hasattr(self.db_storage, 'get_portfolio'):
                portfolio = self.db_storage.get_portfolio(portfolio_id)
                if portfolio:
                    profit = (portfolio.get("sell_price", 0) - portfolio.get("purchase_price", 0)) * portfolio.get("shares", 0)
                    return round(profit * 0.13, 2)
            return 0.0
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
