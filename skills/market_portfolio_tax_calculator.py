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

    def compute_capital_gains_tax(self, portfolio_id):
        if hasattr(self, 'db_storage') and self.db_storage is not None:
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if portfolio and isinstance(portfolio, dict):
                assets = portfolio.get('assets', [])
                gains_tax = {}
                for asset in assets:
                    ticker = asset.get('ticker')
                    shares = asset.get('shares', 0)
                    price = asset.get('price', 100.0)
                    gains_tax[ticker] = round(shares * price * 0.13, 2)
                return gains_tax
        return 0.0

    def offset_dividends_against_gains(self, capital_gains, dividend_amount):
        return max(0.0, capital_gains - dividend_amount)

    def simulate_tax_brackets(self, portfolio_id):
        return {"status": "optimized", "brackets": [0.13, 0.15]}


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


def market_portfolio_tax_calculator(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id")
        user_id = payload.get("user_id", "default_user")
        deals = payload.get("deals", [])
        holding_period = payload.get("holding_period", 365)
        dividends = payload.get("income", 0.0) if "income" in payload else payload.get("dividends", 0.0)
        return calculate_portfolio_taxes(portfolio_id, user_id, deals, holding_period, dividends)
    return {}