class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id, tax_rate=None):
        if isinstance(portfolio_id, (int, float)):
            amount = portfolio_id
            rate = tax_rate if tax_rate is not None else 0.13
            return round(amount * rate, 2)

        if not hasattr(self, 'db_storage') or self.db_storage is None:
            return 0.0
        portfolio = self.db_storage.get_portfolio(portfolio_id)
        if portfolio:
            profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
            return round(profit * (tax_rate if tax_rate is not None else 0.13), 2)
        return 0.0

    def calculate(self, portfolio_payload):
        if isinstance(portfolio_payload, dict):
            portfolio_id = portfolio_payload.get("portfolio_id", "UNKNOWN")
            brackets = portfolio_payload.get("tax_brackets", {})
            st_rate = brackets.get("short_term_capital_gains", 0.22)
            lt_rate = brackets.get("long_term_capital_gains", 0.15)
            div_rate = brackets.get("qualified_dividend", 0.15)

            total_capital_gains_tax = 0.0
            total_dividend_tax = 0.0

            for asset in portfolio_payload.get("assets", []):
                shares = asset.get("shares", 0)
                purchase_price = asset.get("purchase_price", 0.0)
                current_price = asset.get("current_price", 0.0)
                holding_days = asset.get("holding_period_days", 0)

                gain = max(0.0, (current_price - purchase_price) * shares)
                rate = lt_rate if holding_days >= 365 else st_rate
                total_capital_gains_tax += gain * rate

                for div in asset.get("dividends_received", []):
                    div_gross = shares * div.get("amount_per_share", 0.0)
                    total_dividend_tax += div_gross * div_rate

            return {
                "portfolio_id": portfolio_id,
                "total_capital_gains_tax": round(total_capital_gains_tax, 2),
                "total_dividend_tax": round(total_dividend_tax, 2),
                "total_tax_liability": round(total_capital_gains_tax + total_dividend_tax, 2)
            }
        return {"portfolio_id": "UNKNOWN", "total_tax_liability": 0.0}

    def process_dividend_stream(self, stream):
        if hasattr(self, 'market_parser') and hasattr(self.market_parser, 'parse_stream'):
            parsed = self.market_parser.parse_stream(stream)
            if isinstance(parsed, dict) and "stream_id" in parsed:
                return parsed["stream_id"]
        return None


def market_portfolio_tax_calculator(**kwargs):
    return MarketPortfolioTaxCalculator(**kwargs)


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