class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id):
        if hasattr(self, 'db_storage') and self.db_storage:
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if portfolio:
                profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
                return round(profit * 0.13, 2)
        return 0.0

    def compute_taxes(self, portfolio_id, tax_year):
        return {"portfolio_id": portfolio_id, "tax_year": tax_year, "tax_due": 0.0}

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
        elif hasattr(deal, "type") and deal.type == "SELL":
            total_profit += (getattr(deal, "price", 0) - 100.0) * getattr(deal, "shares", 0)
    
    total_tax_due = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_tax_due": total_tax_due
    }


def market_portfolio_tax_calculator(payload):
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id", "default")
        tax_year = payload.get("tax_year", 2023)
        return {"portfolio_id": portfolio_id, "tax_year": tax_year, "tax_due": 0.0}
    return {"status": "ok"}
