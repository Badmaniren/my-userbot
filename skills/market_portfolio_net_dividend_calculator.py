from skills.market_portfolio_dividend_tracker import DividendTracker, DividendTrackerException
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator

class NetDividendCalculatorException(Exception):
    """Исключение для калькулятора чистых дивидендов."""
    pass

class NetDividendCalculator:
    def __init__(self, db_storage=None, dividend_tracker=None, tax_calculator=None, api_gateway=None):
        self.db_storage = db_storage
        self.api_gateway = api_gateway
        self.dividend_tracker = dividend_tracker if dividend_tracker is not None else DividendTracker(
            db_storage=self.db_storage,
            tax_calculator=tax_calculator,
            api_gateway=self.api_gateway
        )
        self.tax_calculator = tax_calculator if tax_calculator is not None else MarketPortfolioTaxCalculator()

    def calculate_net_dividend_yield(self, portfolio_id, asset_ticker, shares_count, asset_price=None, tax_rate=None):
        try:
            tracker_kwargs = {
                'asset_ticker': asset_ticker,
                'shares_count': shares_count
            }
            if tax_rate is not None:
                tracker_kwargs['tax_rate'] = tax_rate

            dividend_data = self.dividend_tracker.calculate_projected_dividends(**tracker_kwargs)
            
            gross_dividend = dividend_data.get('gross_dividend', 0.0)
            
            tax_data = self.tax_calculator.calculate_tax(
                portfolio_id=portfolio_id,
                gross_amount=gross_dividend
            )
            
            tax_amount = tax_data.get('tax_amount', 0.0)
            net_dividend_amount = gross_dividend - tax_amount
            
            net_dividend_yield = 0.0
            if asset_price is not None and shares_count > 0 and asset_price > 0:
                net_dividend_yield = net_dividend_amount / (shares_count * asset_price)

            return {
                'ticker': dividend_data.get('ticker', asset_ticker),
                'shares': dividend_data.get('shares', shares_count),
                'net_dividend_amount': net_dividend_amount,
                'net_dividend_yield': net_dividend_yield
            }
        except DividendTrackerException as e:
            raise NetDividendCalculatorException(str(e))
        except Exception as e:
            if isinstance(e, NetDividendCalculatorException):
                raise
            raise NetDividendCalculatorException(str(e))

    def aggregate_net_dividends_for_portfolio(self, portfolio_id):
        try:
            dividends_list = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)
            
            tax_stream_result = self.tax_calculator.process_dividend_stream(dividends_list)
            
            total_net = tax_stream_result.get('total_net', 0.0)

            return {
                'portfolio_id': portfolio_id,
                'total_net_dividends': total_net
            }
        except Exception as e:
            raise NetDividendCalculatorException(str(e))