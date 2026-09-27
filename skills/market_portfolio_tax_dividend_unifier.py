from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker


class TaxDividendUnifierException(Exception):
    pass


class TaxDividendUnifier:
    def __init__(self, db_storage=None, tax_calculator=None, dividend_tracker=None):
        self.db_storage = db_storage
        self.tax_calculator = tax_calculator or MarketPortfolioTaxCalculator(db_storage=db_storage)
        self.dividend_tracker = dividend_tracker or DividendTracker(db_storage=db_storage)

        if self.db_storage is not None:
            if getattr(self.tax_calculator, 'db_storage', None) is None:
                self.tax_calculator.db_storage = self.db_storage
            if getattr(self.dividend_tracker, 'db_storage', None) is None:
                self.dividend_tracker.db_storage = self.db_storage

    def calculate_net_yield(self, portfolio_id: str) -> dict:
        try:
            tax_result = self.tax_calculator.calculate_tax(portfolio_id)
            dividends_result = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)

            if isinstance(tax_result, dict):
                total_tax = tax_result.get("total_tax", tax_result.get("tax_withheld", 0.0))
            elif isinstance(tax_result, (int, float)):
                total_tax = float(tax_result)
            else:
                total_tax = getattr(tax_result, "total_tax", getattr(tax_result, "tax_withheld", 0.0))

            if isinstance(dividends_result, dict):
                total_dividends = dividends_result.get("total_dividends", dividends_result.get("total_net_dividends", 0.0))
            elif isinstance(dividends_result, (int, float)):
                total_dividends = float(dividends_result)
            else:
                total_dividends = getattr(dividends_result, "total_dividends", getattr(dividends_result, "total_net_dividends", 0.0))

            net_yield = round(total_dividends - total_tax, 2)

            return {
                "portfolio_id": portfolio_id,
                "tax_withheld": total_tax,
                "gross_dividends": total_dividends,
                "net_yield": net_yield
            }
        except Exception as e:
            if isinstance(e, TaxDividendUnifierException):
                raise e
            raise TaxDividendUnifierException(str(e))

    def process_stream_data(self, stream_data) -> bool:
        self.tax_calculator.process_dividend_stream(stream_data)
        if hasattr(self.dividend_tracker, "process_dividends") and callable(getattr(self.dividend_tracker, "process_dividends")):
            self.dividend_tracker.process_dividends(stream_data)
        elif hasattr(self.dividend_tracker, "process_dividend_stream") and callable(getattr(self.dividend_tracker, "process_dividend_stream")):
            self.dividend_tracker.process_dividend_stream(stream_data)
        else:
            if hasattr(self.dividend_tracker, "process_stream_data") and callable(getattr(self.dividend_tracker, "process_stream_data")):
                self.dividend_tracker.process_stream_data(stream_data)
        return True


def unify_portfolio_yield(portfolio_id: str, user_id: str = None) -> dict:
    tax_calc = MarketPortfolioTaxCalculator()
    div_track = DividendTracker()

    tax_result = tax_calc.calculate_tax(portfolio_id)
    dividends_result = div_track.aggregate_portfolio_dividends(portfolio_id)

    total_tax = tax_result.get("total_tax", 0.0) if isinstance(tax_result, dict) else getattr(tax_result, "total_tax", 0.0)
    total_dividends = dividends_result.get("total_dividends", 0.0) if isinstance(dividends_result, dict) else getattr(dividends_result, "total_dividends", 0.0)

    net_yield = round(total_dividends - total_tax, 2)

    return {
        "portfolio_id": portfolio_id,
        "tax_withheld": total_tax,
        "gross_dividends": total_dividends,
        "net_yield": net_yield
    }


def unifier_pipeline(portfolio_id: str, user_id: str, asset_ticker: str, shares_count: int, tax_rate: float, dividend_stream: list) -> dict:
    total_dividends = sum(item.get("amount", 0.0) for item in dividend_stream)
    total_tax = round(total_dividends * tax_rate, 2)
    net_yield = round(total_dividends - total_tax, 2)

    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "asset_ticker": asset_ticker,
        "shares_count": shares_count,
        "tax_rate": tax_rate,
        "dividend_stream": dividend_stream,
        "total_dividends": total_dividends,
        "total_tax": total_tax,
        "net_yield": net_yield
    }