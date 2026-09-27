from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker


class TaxDividendSyncException(Exception):
    """Custom exception for Tax Dividend Synchronization errors."""
    pass


class TaxDividendSync:
    def __init__(self, db_storage=None, api_gateway=None):
        self.db_storage = db_storage
        self.api_gateway = api_gateway
        self.tax_calculator = MarketPortfolioTaxCalculator()
        self.dividend_tracker = DividendTracker(
            db_storage=db_storage,
            tax_calculator=self.tax_calculator,
            api_gateway=api_gateway
        )

    def calculate_synchronized_net_yield(self, portfolio_id, asset_ticker, shares_count, tax_rate):
        try:
            gross_dividends = self.dividend_tracker.calculate_projected_dividends(
                asset_ticker=asset_ticker,
                shares_count=shares_count,
                tax_rate=tax_rate
            )
            gross_val = gross_dividends.get("gross_dividend", 0.0) if isinstance(gross_dividends, dict) else gross_dividends
            if hasattr(self.tax_calculator, "calculate_tax"):
                try:
                    calculated_tax = self.tax_calculator.calculate_tax(gross_val, tax_rate)
                except TypeError:
                    calculated_tax = self.tax_calculator.calculate_tax(gross_val)
            else:
                calculated_tax = round(gross_val * tax_rate, 2)

            net_yield = round(gross_val - calculated_tax, 2)

            return {
                'net_yield': net_yield,
                'gross_dividends': gross_val,
                'calculated_tax': calculated_tax
            }
        except Exception as e:
            if isinstance(e, TaxDividendSyncException):
                raise e
            raise TaxDividendSyncException(str(e))

    def synchronize_portfolio_audit_flow(self, portfolio_id, user_id, stream_source):
        dividends = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)
        tax_report = self.tax_calculator.process_dividend_stream(stream_source)

        return {
            'portfolio_id': portfolio_id,
            'dividends': dividends,
            'tax_report': tax_report
        }


class PortfolioTaxDividendSyncManager:
    def __init__(self, db_storage=None, tax_calculator=None, dividend_tracker=None):
        self.db_storage = db_storage
        self.tax_calculator = tax_calculator or MarketPortfolioTaxCalculator()
        self.dividend_tracker = dividend_tracker or DividendTracker(
            db_storage=db_storage,
            tax_calculator=self.tax_calculator
        )

    def process_sync_cycle(self, portfolio_id, dividend_stream):
        total_dividends = 0.0
        for item in dividend_stream:
            total_dividends += item.get("amount", 0.0)

        return {
            "synchronized": True,
            "portfolio_id": portfolio_id,
            "total_dividends": total_dividends
        }


def sync_portfolio_tax_and_dividends(
    portfolio_id,
    owner_uuid,
    asset_ticker,
    shares_count,
    tax_rate,
    dividend_stream,
    db_storage=None
):
    tax_calculator = MarketPortfolioTaxCalculator()

    dividend_tracker = DividendTracker(
        db_storage=db_storage,
        tax_calculator=tax_calculator,
        api_gateway=None
    )

    total_dividends = sum(item.get("amount", 0.0) for item in dividend_stream)
    total_tax = round(total_dividends * tax_rate, 2)
    net_yield = round(total_dividends - total_tax, 2)

    return {
        "portfolio_id": portfolio_id,
        "owner_uuid": owner_uuid,
        "total_dividends": total_dividends,
        "total_tax": total_tax,
        "net_yield": net_yield
    }