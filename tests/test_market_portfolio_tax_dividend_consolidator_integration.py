import unittest
import uuid
import random
from skills.market_portfolio_tax_dividend_consolidator import consolidate_portfolio_financials
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker


class TestMarketPortfolioTaxDividendConsolidatorIntegration(unittest.TestCase):

    def test_consolidate_portfolio_financials_integration(self):
        test_portfolio_id = str(uuid.uuid4())
        test_user_id = str(uuid.uuid4())
        test_asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        test_shares_count = random.randint(10, 500)
        test_tax_rate = round(random.uniform(0.09, 0.20), 2)

        tax_calc = MarketPortfolioTaxCalculator()
        div_tracker = DividendTracker(db_storage=None, tax_calculator=tax_calc, api_gateway=None)

        result = consolidate_portfolio_financials(
            portfolio_id=test_portfolio_id,
            user_id=test_user_id,
            asset_ticker=test_asset_ticker,
            shares_count=test_shares_count,
            tax_rate=test_tax_rate
        )

        self.assertIsInstance(result, dict)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], test_portfolio_id)
        self.assertIn("tax_report", result)
        self.assertIn("dividend_report", result)
        self.assertIn("consolidated_total", result)

        projected_divs = div_tracker.calculate_projected_dividends(
            asset_ticker=test_asset_ticker,
            shares_count=test_shares_count,
            tax_rate=test_tax_rate
        )
        self.assertIsNotNone(projected_divs)


if __name__ == "__main__":
    unittest.main()