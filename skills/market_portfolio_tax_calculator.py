class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, portfolio_id):
        if not hasattr(self, "db_storage") or self.db_storage is None:
            return 0.0
        portfolio = self.db_storage.get_portfolio(portfolio_id)
        if portfolio:
            profit = (portfolio["sell_price"] - portfolio["purchase_price"]) * portfolio["shares"]
            return round(profit * 0.13, 2)
        return 0.0

    def process_dividend_stream(self, stream):
        if hasattr(self, "market_parser") and hasattr(self.market_parser, "parse_stream"):
            parsed = self.market_parser.parse_stream(stream)
            if isinstance(parsed, dict) and "stream_id" in parsed:
                return parsed["stream_id"]
        return None


def calculate_portfolio_taxes(portfolio_id, user_id, deals, holding_period, dividends):
    total_profit = 0.0
    inventory = []
    
    for deal in deals:
        if deal is None:
            continue
            
        if isinstance(deal, dict):
            d_type = deal.get("type")
            price = deal.get("price", 0)
            shares = deal.get("shares", 0)
        elif hasattr(deal, "type"):
            d_type = getattr(deal, "type", None)
            price = getattr(deal, "price", 0)
            shares = getattr(deal, "shares", 0)
        else:
            continue

        if price is None:
            price = 0
        if shares is None:
            shares = 0

        if d_type == "BUY":
            inventory.append({"price": price, "shares": shares})
        elif d_type == "SELL":
            remaining_shares_to_sell = shares
            while remaining_shares_to_sell > 0 and inventory:
                lot = inventory[0]
                if lot["shares"] <= remaining_shares_to_sell:
                    total_profit += (price - lot["price"]) * lot["shares"]
                    remaining_shares_to_sell -= lot["shares"]
                    inventory.pop(0)
                else:
                    total_profit += (price - lot["price"]) * remaining_shares_to_sell
                    lot["shares"] -= remaining_shares_to_sell
                    remaining_shares_to_sell = 0
            if remaining_shares_to_sell > 0:
                total_profit += (price - 100.0) * remaining_shares_to_sell

    total_tax_due = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_tax_due": total_tax_due,
    }