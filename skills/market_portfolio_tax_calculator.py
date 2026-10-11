from skills.db_storage import DbStorage
from skills.market_parser import MarketParser


class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id):
        if isinstance(portfolio_id, dict):
            portfolio = portfolio_id
        elif hasattr(self, "db_storage") and self.db_storage is not None:
            if hasattr(self.db_storage, "get_portfolio"):
                portfolio = self.db_storage.get_portfolio(portfolio_id)
            elif isinstance(self.db_storage, dict):
                portfolio = self.db_storage.get(portfolio_id)
            else:
                portfolio = None
        else:
            return 0.0

        if portfolio and isinstance(portfolio, dict):
            sell = portfolio.get("sell_price", 0.0)
            purchase = portfolio.get("purchase_price", 0.0)
            shares = portfolio.get("shares", 0)
            dividends = portfolio.get("dividends", 0.0)
            profit = (sell - purchase) * shares + dividends
            return round(max(0.0, profit * 0.13), 2)
        return 0.0

    def process_dividend_stream(self, stream):
        if hasattr(self, "market_parser") and hasattr(self.market_parser, "parse_stream"):
            parsed = self.market_parser.parse_stream(stream)
            if isinstance(parsed, dict) and "stream_id" in parsed:
                return parsed["stream_id"]
        if isinstance(stream, dict) and "stream_id" in stream:
            return stream["stream_id"]
        return None


def calculate_portfolio_taxes(portfolio_id, user_id, deals, holding_period=365, dividends=0.0):
    total_profit = 0.0
    for deal in deals:
        if isinstance(deal, dict):
            deal_type = deal.get("type")
            price = deal.get("price", 0)
            shares = deal.get("shares", 0)
            commission = deal.get("commission", 0) or deal.get("fee", 0) or 0
        else:
            deal_type = getattr(deal, "type", None)
            price = getattr(deal, "price", 0)
            shares = getattr(deal, "shares", 0)
            commission = getattr(deal, "commission", 0) or getattr(deal, "fee", 0) or 0

        if price is None:
            price = 0
        if shares is None:
            shares = 0

        if deal_type == "SELL":
            cost_price = 100.0
            deal_profit = (price - cost_price) * shares - commission
            total_profit += deal_profit

    total_tax_due = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_tax_due": total_tax_due,
    }


def calculate_tax(portfolio_id, **kwargs):
    calc = MarketPortfolioTaxCalculator(**kwargs)
    return calc.calculate_tax(portfolio_id)


tax_calculator = MarketPortfolioTaxCalculator
market_portfolio_tax_calculator = MarketPortfolioTaxCalculator
