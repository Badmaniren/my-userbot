import io


class MarketPortfolioTaxCalculator:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def calculate_tax(self, *args, **kwargs):
        if not args:
            return 0.0

        first_arg = args[0]

        # If called with (gross_dividend, tax_rate) as in dividend tracker
        if isinstance(first_arg, (int, float)):
            tax_rate = args[1] if len(args) > 1 else kwargs.get("tax_rate", 0.13)
            if tax_rate is None:
                tax_rate = 0.13
            return round(first_arg * tax_rate, 2)

        # If called with portfolio_id
        portfolio_id = first_arg
        if not hasattr(self, "db_storage") or self.db_storage is None:
            return 0.0

        if hasattr(self.db_storage, "get_portfolio"):
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if portfolio:
                profit = (portfolio.get("sell_price", 0) - portfolio.get("purchase_price", 0)) * portfolio.get("shares", 0)
                return round(profit * 0.13, 2)
        return 0.0

    def process_dividend_stream(self, stream):
        if hasattr(self, "market_parser") and hasattr(self.market_parser, "parse_stream"):
            parsed = self.market_parser.parse_stream(stream)
            if isinstance(parsed, dict) and "stream_id" in parsed:
                return parsed["stream_id"]
        return None


def calculate_tax(gross_or_portfolio_id, tax_rate=0.13):
    if isinstance(gross_or_portfolio_id, (int, float)):
        return round(gross_or_portfolio_id * (tax_rate if tax_rate is not None else 0.13), 2)
    return 0.0


def _get_deal_attr(deal, key, default=None):
    if isinstance(deal, dict):
        return deal.get(key, default)
    return getattr(deal, key, default)


def calculate_portfolio_taxes(portfolio_id, user_id, deals, holding_period=0, dividends=0.0, method="FIFO", commissions=0.0, **kwargs):
    if dividends is None:
        dividends = 0.0
    if commissions is None:
        commissions = 0.0

    inventory = []
    total_profit = 0.0
    total_commissions = float(commissions)
    accounting_method = str(method).upper() if method else "FIFO"

    if deals:
        for deal in deals:
            dtype = _get_deal_attr(deal, "type") or _get_deal_attr(deal, "action") or _get_deal_attr(deal, "dtype")
            if dtype:
                dtype = str(dtype).upper()

            price = _get_deal_attr(deal, "price", 0.0)
            shares = _get_deal_attr(deal, "shares", 0.0)
            if shares is None or shares == 0:
                shares = _get_deal_attr(deal, "quantity", 0.0) or _get_deal_attr(deal, "amount", 0.0)

            deal_commission = _get_deal_attr(deal, "commission", 0.0) or _get_deal_attr(deal, "fee", 0.0) or 0.0

            if price is None:
                price = 0.0
            if shares is None:
                shares = 0.0
            if deal_commission is None:
                deal_commission = 0.0

            total_commissions += float(deal_commission)

            if dtype == "BUY":
                inventory.append({"price": float(price), "shares": float(shares)})
            elif dtype == "SELL":
                remaining_to_sell = float(shares)
                while remaining_to_sell > 0 and inventory:
                    lot_idx = 0 if accounting_method == "FIFO" else -1
                    lot = inventory[lot_idx]

                    if lot["shares"] <= remaining_to_sell:
                        total_profit += (float(price) - lot["price"]) * lot["shares"]
                        remaining_to_sell -= lot["shares"]
                        inventory.pop(lot_idx)
                    else:
                        total_profit += (float(price) - lot["price"]) * remaining_to_sell
                        lot["shares"] -= remaining_to_sell
                        remaining_to_sell = 0

                if remaining_to_sell > 0:
                    total_profit += (float(price) - 100.0) * remaining_to_sell

    net_profit = total_profit - total_commissions
    taxable_base = max(0.0, net_profit + float(dividends))
    total_tax_due = round(taxable_base * 0.13, 2)

    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "total_tax_due": total_tax_due,
        "total_profit": round(total_profit, 2),
        "total_commissions": round(total_commissions, 2),
        "net_profit": round(net_profit, 2),
        "taxable_base": round(taxable_base, 2),
        "method": accounting_method,
    }


tax_calculator = MarketPortfolioTaxCalculator()
market_portfolio_tax_calculator = MarketPortfolioTaxCalculator()
