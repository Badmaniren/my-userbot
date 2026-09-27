import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker
from skills import market_portfolio_tax_dividend_report

class TestMarketPortfolioTaxDividendReportIntegration(unittest.TestCase):
    def test_tax_dividend_report_composition(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        mock_db = object()
        mock_api = object()

        tax_calc = MarketPortfolioTaxCalculator()
        dividend_tracker = DividendTracker(db_storage=mock_db, tax_calculator=tax_calc, api_gateway=mock_api)

        random_shares = random.randint(10, 1000)
        random_tax_rate = round(random.uniform(0.09, 0.2), 2)
        ticker = f"TICK_{random.randint(100, 999)}"

        projected = dividend_tracker.calculate_projected_dividends(
            asset_ticker=ticker,
            shares_count=random_shares,
            tax_rate=random_tax_rate
        )

        tax_result = tax_calc.calculate_tax(portfolio_id=portfolio_id)

        report_data = market_portfolio_tax_dividend_report.generate_report(
            portfolio_id=portfolio_id,
            user_id=user_id,
            tax_data=tax_result,
            dividend_data=projected
        )

        self.assertIsNotNone(report_data)
        self.assertIn(portfolio_id, str(report_data))

if __name__ == '__main__':
    unittest.main()