import unittest
import uuid
import random
from skills import market_portfolio_dividend_tracker
from skills import market_portfolio_tax_calculator
from skills import db_storage


class TestDividendTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = db_storage
        self.tax_calc = market_portfolio_tax_calculator
        self.tracker = market_portfolio_dividend_tracker.DividendTracker(
            db_storage=self.db,
            tax_calculator=self.tax_calc,
            api_gateway=None
        )

    def test_calculate_projected_dividends_integration_error(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_shares = random.randint(10, 1000)
        random_tax_rate = round(random.uniform(0.05, 0.25), 2)

        with self.assertRaises(Exception):
            self.tracker.calculate_projected_dividends(
                random_ticker, 
                random_shares, 
                random_tax_rate
            )

    def test_process_dividends_data_flow(self):
        random_portfolio_id = str(uuid.uuid4())
        random_asset = f"ASSET_{uuid.uuid4().hex[:4].upper()}"
        random_amount = round(random.uniform(100.0, 50000.0), 2)

        result = market_portfolio_dividend_tracker.process_dividends(
            random_portfolio_id,
            random_asset,
            random_amount
        )

        self.assertIn("dividend_id", result)
        self.assertEqual(result["asset"], random_asset)
        self.assertEqual(result["amount"], random_amount)
        self.assertTrue(result["dividend_id"].endswith(random_portfolio_id))

    def test_get_dividend_calendar_structure(self):
        random_owner_uuid = str(uuid.uuid4())
        random_month = random.randint(1, 12)
        random_year = random.randint(2024, 2030)

        calendar = self.tracker.get_dividend_calendar(
            random_owner_uuid,
            random_month,
            random_year
        )

        self.assertEqual(calendar["owner"], random_owner_uuid)
        self.assertEqual(calendar["month"], random_month)
        self.assertEqual(calendar["year"], random_year)
        self.assertIsInstance(calendar["calendar_entries"], list)


if __name__ == "__main__":
    unittest.main()