import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_dividend_tracker import DividendTracker, DividendTrackerException, process_dividends

class TestDividendTracker(unittest.TestCase):
    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.tax_calculator_mock = MagicMock()
        self.api_gateway_mock = MagicMock()
        self.tracker = DividendTracker(
            db_storage=self.db_storage_mock,
            tax_calculator=self.tax_calculator_mock,
            api_gateway=self.api_gateway_mock
        )

    def test_calculate_projected_dividends_success(self):
        ticker = uuid.uuid4().hex[:6].upper()
        shares_count = random.randint(10, 1000)
        tax_rate = round(random.uniform(0.05, 0.30), 2)
        dividend_per_share = round(random.uniform(0.5, 15.0), 2)
        
        self.api_gateway_mock.get_dividend_info.return_value = {
            "dividend_per_share": dividend_per_share
        }
        
        expected_gross = shares_count * dividend_per_share
        expected_tax = round(expected_gross * tax_rate, 2)
        expected_net = expected_gross - expected_tax
        
        self.tax_calculator_mock.calculate_tax.return_value = expected_tax

        result = self.tracker.calculate_projected_dividends(ticker, shares_count, tax_rate)

        self.assertEqual(result["ticker"], ticker)
        self.assertEqual(result["gross_dividend"], expected_gross)
        self.assertEqual(result["tax_withheld"], expected_tax)
        self.assertEqual(result["net_dividend"], expected_net)
        self.api_gateway_mock.get_dividend_info.assert_called_once_with(ticker)
        self.tax_calculator_mock.calculate_tax.assert_called_once_with(expected_gross, tax_rate)

    def test_fetch_and_store_dividend_history(self):
        asset_id = uuid.uuid4().hex
        self.tracker.fetch_and_store_dividend_history(asset_id)
        self.api_gateway_mock.pull_raw_stream.assert_called_once_with(asset_id)

    def test_aggregate_portfolio_dividends(self):
        portfolio_id = uuid.uuid4().hex
        asset_count = random.randint(2, 5)
        assets = []
        total_expected_net = 0.0

        for _ in range(asset_count):
            ticker = uuid.uuid4().hex[:5].upper()
            shares = random.randint(1, 100)
            dps = round(random.uniform(1.0, 10.0), 2)
            tax_rate = round(random.uniform(0.0, 0.2), 2)
            
            gross = shares * dps
            tax = round(gross * tax_rate, 2)
            net = gross - tax
            total_expected_net += net

            assets.append({
                "ticker": ticker,
                "shares": shares,
                "dividend_per_share": dps,
                "tax_rate": tax_rate
            })

        self.db_storage_mock.get_portfolio_assets.return_value = assets
        self.tax_calculator_mock.calculate_tax.side_effect = [
            round(a["shares"] * a["dividend_per_share"] * a["tax_rate"], 2) for a in assets
        ]

        result = self.tracker.aggregate_portfolio_dividends(portfolio_id)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertAlmostEqual(result["total_net_dividends"], total_expected_net, places=5)
        self.db_storage_mock.get_portfolio_assets.assert_called_once_with(portfolio_id)

    def test_get_dividend_calendar(self):
        owner_uuid = uuid.uuid4().hex
        month = random.randint(1, 12)
        year = random.randint(2020, 2030)
        random_url = f"http://{uuid.uuid4().hex}.com/calendar"

        with patch("requests.get") as mock_get:
            result = self.tracker.get_dividend_calendar(owner_uuid, month, year)
            
            self.assertEqual(result["owner"], owner_uuid)
            self.assertEqual(result["month"], month)
            self.assertEqual(result["year"], year)
            self.assertIsInstance(result["calendar_entries"], list)

    def test_process_dividends(self):
        portfolio_id = uuid.uuid4().hex
        asset = uuid.uuid4().hex[:6].upper()
        amount = round(random.uniform(10.0, 5000.0), 2)

        result = process_dividends(portfolio_id, asset, amount)

        self.assertEqual(result["dividend_id"], f"div_{portfolio_id}")
        self.assertEqual(result["asset"], asset)
        self.assertEqual(result["amount"], amount)

if __name__ == "__main__":
    unittest.main()