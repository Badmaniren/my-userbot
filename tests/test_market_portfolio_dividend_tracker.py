import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import requests

from skills.market_portfolio_dividend_tracker import (
    DividendTracker,
    DividendTrackerException,
    process_dividends
)
from skills import db_storage


class TestMarketPortfolioDividendTracker(unittest.TestCase):

    def setUp(self):
        self.db_mock = MagicMock()
        self.tax_calc_mock = MagicMock()
        self.api_gateway_mock = MagicMock()
        self.tracker = DividendTracker(
            db_storage=self.db_mock,
            tax_calculator=self.tax_calc_mock,
            api_gateway=self.api_gateway_mock
        )

    def test_calculate_projected_dividends_success(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        shares_count = random.randint(10, 1000)
        tax_rate = round(random.uniform(0.05, 0.20), 2)
        dividend_per_share = round(random.uniform(1.0, 50.0), 2)

        self.api_gateway_mock.get_dividend_info.return_value = {
            "dividend_per_share": dividend_per_share
        }

        gross = shares_count * dividend_per_share
        simulated_tax = round(gross * tax_rate, 2)
        self.tax_calc_mock.calculate_tax.return_value = simulated_tax

        result = self.tracker.calculate_projected_dividends(ticker, shares_count, tax_rate)

        self.assertEqual(result["ticker"], ticker)
        self.assertEqual(result["gross_dividend"], gross)
        self.assertEqual(result["tax_withheld"], simulated_tax)
        self.assertEqual(result["net_dividend"], gross - simulated_tax)

        self.api_gateway_mock.get_dividend_info.assert_called_once_with(ticker)
        self.tax_calc_mock.calculate_tax.assert_called_once_with(gross, tax_rate)

    def test_fetch_and_store_dividend_history_exception(self):
        asset_id = uuid.uuid4().hex
        self.api_gateway_mock.pull_raw_stream.side_effect = DividendTrackerException(uuid.uuid4().hex)

        with self.assertRaises(DividendTrackerException):
            self.tracker.fetch_and_store_dividend_history(asset_id)

        self.api_gateway_mock.pull_raw_stream.assert_called_once_with(asset_id)

    def test_aggregate_portfolio_dividends_calculation(self):
        portfolio_id = uuid.uuid4().hex
        asset_count = random.randint(1, 5)
        
        assets = []
        expected_total_net = 0.0

        for _ in range(asset_count):
            shares = random.randint(5, 100)
            dps = round(random.uniform(0.5, 10.0), 2)
            tax_rate = round(random.uniform(0.0, 0.15), 2)
            gross = shares * dps
            tax = round(gross * tax_rate, 2)
            net = gross - tax
            expected_total_net += net

            assets.append({
                "ticker": f"T_{uuid.uuid4().hex[:4]}",
                "shares": shares,
                "dividend_per_share": dps,
                "tax_rate": tax_rate
            })

        self.db_mock.get_portfolio_assets.return_value = assets
        self.tax_calc_mock.calculate_tax.side_effect = [
            round(a["shares"] * a["dividend_per_share"] * a["tax_rate"], 2) for a in assets
        ]

        result = self.tracker.aggregate_portfolio_dividends(portfolio_id)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertAlmostEqual(result["total_net_dividends"], expected_total_net, places=5)
        self.db_mock.get_portfolio_assets.assert_called_once_with(portfolio_id)

    def test_get_dividend_calendar_requests(self):
        owner_uuid = uuid.uuid4().hex
        month = random.randint(1, 12)
        year = random.randint(2020, 2030)

        with patch("skills.market_portfolio_dividend_tracker.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.tracker.get_dividend_calendar(owner_uuid, month, year)

            self.assertEqual(result["owner"], owner_uuid)
            self.assertEqual(result["month"], month)
            self.assertEqual(result["year"], year)
            self.assertIn("calendar_entries", result)
            mock_get.assert_called_once()

    def test_process_dividends_integration_helpers(self):
        portfolio_id = uuid.uuid4().hex
        asset_name = f"ASSET_{uuid.uuid4().hex[:6]}"
        amount = round(random.uniform(100.0, 5000.0), 2)

        if hasattr(db_storage, "save_record"):
            delattr(db_storage, "save_record")
        if hasattr(db_storage, "export_to_file"):
            delattr(db_storage, "export_to_file")

        result = process_dividends(portfolio_id, asset_name, amount)

        self.assertEqual(result["dividend_id"], f"div_{portfolio_id}")
        self.assertEqual(result["asset"], asset_name)
        self.assertEqual(result["amount"], amount)

        self.assertTrue(hasattr(db_storage, "save_record"))
        self.assertTrue(hasattr(db_storage, "export_to_file"))


if __name__ == "__main__":
    unittest.main()