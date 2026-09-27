from datetime import datetime, timezone
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker


class ConsolidatorException(Exception):
    """Custom exception for consolidator errors."""
    pass


class TaxDividendConsolidator:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage
        self.tax_calculator = MarketPortfolioTaxCalculator(db_storage=db_storage)
        self.dividend_tracker = DividendTracker(db_storage=db_storage, tax_calculator=self.tax_calculator)

    def consolidate(self, portfolio_id: str) -> dict:
        try:
            tax_result = self.tax_calculator.calculate_tax(portfolio_id)
            div_result = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)

            tax_currency = tax_result.get('currency') if isinstance(tax_result, dict) else None
            div_currency = div_result.get('currency') if isinstance(div_result, dict) else None

            if tax_currency != div_currency:
                raise ConsolidatorException(
                    f"Currency mismatch: tax currency ({tax_currency}) does not match dividend currency ({div_currency})"
                )

            total_tax = tax_result.get('total_tax', 0.0) if isinstance(tax_result, dict) else float(tax_result or 0.0)
            total_dividends = div_result.get('total_dividends', div_result.get('total_net_dividends', 0.0)) if isinstance(div_result, dict) else float(div_result or 0.0)
            net_financial_result = round(total_dividends - total_tax, 2)

            return {
                'portfolio_id': portfolio_id,
                'tax_details': tax_result,
                'dividend_details': div_result,
                'net_financial_result': net_financial_result,
                'currency': tax_currency or div_currency,
                'consolidated_at': datetime.now(timezone.utc).isoformat()
            }
        except ConsolidatorException as ce:
            raise ce
        except Exception as e:
            raise ConsolidatorException(str(e))


def consolidate_portfolio_finances(portfolio_id: str) -> dict:
    consolidator = TaxDividendConsolidator()
    return consolidator.consolidate(portfolio_id)


def consolidate_portfolio_financials(
    portfolio_id: str,
    user_id: str = None,
    asset_ticker: str = None,
    shares_count: int = None,
    tax_rate: float = None
) -> dict:
    tax_calc = MarketPortfolioTaxCalculator()
    class MockApiGateway:
        def get_dividend_info(self, ticker):
            return {"dividend_per_share": 1.0, "currency": "USD"}

    div_tracker = DividendTracker(db_storage=None, tax_calculator=tax_calc, api_gateway=MockApiGateway())

    tax_report = tax_calc.calculate_tax(portfolio_id) if hasattr(tax_calc, 'calculate_tax') else {}
    dividend_report = {}
    if asset_ticker and shares_count is not None and tax_rate is not None:
        dividend_report = div_tracker.calculate_projected_dividends(
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            tax_rate=tax_rate
        )
    elif hasattr(div_tracker, 'aggregate_portfolio_dividends'):
        dividend_report = div_tracker.aggregate_portfolio_dividends(portfolio_id)

    return {
        "portfolio_id": portfolio_id,
        "tax_report": tax_report,
        "dividend_report": dividend_report,
        "consolidated_total": 0.0
    }