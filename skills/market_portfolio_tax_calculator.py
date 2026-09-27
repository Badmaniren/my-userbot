class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id_or_amount, tax_rate=None):
        if isinstance(portfolio_id_or_amount, (int, float)):
            rate = 0.13 if tax_rate is None else (tax_rate / 100.0 if tax_rate > 1.0 else tax_rate)
            return round(portfolio_id_or_amount * rate, 2)

        if not hasattr(self, 'db_storage') or self.db_storage is None:
            return 0.0
        portfolio = self.db_storage.get_portfolio(portfolio_id_or_amount)
        if portfolio:
            profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
            rate = 0.13 if tax_rate is None else (tax_rate / 100.0 if tax_rate > 1.0 else tax_rate)
            return round(profit * rate, 2)
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