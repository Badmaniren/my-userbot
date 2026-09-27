import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_dividend_tracker import (
    DividendTracker,
    DividendTrackerException,
)


class TestMarketPortfolioDividendTracker(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.tax_calculator = MagicMock()
        self.api_gateway = MagicMock()
        self.tracker = DividendTracker(
            db_storage=self.db_storage,
            tax_calculator=self.tax_calculator,
            api_gateway=self.api_gateway,
        )

    def test_calculate_projected_dividends_success(self):
        asset_ticker = "".join(random.choices(string.ascii_uppercase, k=4))
        shares_count = random.randint(10, 1000)
        dividend_per_share = round(random.uniform(1.0, 50.0), 2)
        tax_rate = round(random.uniform(0.05, 0.30), 2)

        expected_gross = shares_count * dividend_per_share
        expected_tax = expected_gross * tax_rate
        expected_net = expected_gross - expected_tax

        self.api_gateway.get_dividend_info.return_value = {
            "ticker": asset_ticker,
            "dividend_per_share": dividend_per_share,
            "currency": "USD",
        }
        self.tax_calculator.calculate_tax.return_value = expected_tax

        result = self.tracker.calculate_projected_dividends(
            asset_ticker, shares_count, tax_rate
        )

        self.assertEqual(result["ticker"], asset_ticker)
        self.assertEqual(result["gross_dividend"], expected_gross)
        self.assertEqual(result["tax_withheld"], expected_tax)
        self.assertEqual(result["net_dividend"], expected_net)
        self.tax_calculator.calculate_tax.assert_called_once_with(
            expected_gross, tax_rate
        )

    def test_fetch_and_store_dividend_history_io_error(self):
        asset_id = str(uuid.uuid4())
        mock_stream = io.BytesIO(
            b"Invalid payload data stream for asset " + asset_id.encode()
        )

        with patch("skills.market_portfolio_dividend_tracker.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            self.api_gateway.pull_raw_stream.side_effect = (
                DividendTrackerException("Stream failure")
            )

            with self.assertRaises(DividendTrackerException):
                self.tracker.fetch_and_store_dividend_history(asset_id)

    def test_portfolio_dividend_aggregation(self):
        portfolio_id = uuid.uuid4().hex
        assets_count = random.randint(3, 8)
        portfolio_assets = []
        total_expected_net = 0.0

        for _ in range(assets_count):
            ticker = "".join(random.choices(string.ascii_uppercase, k=5))
            shares = random.randint(50, 500)
            dps = round(random.uniform(0.5, 10.0), 2)
            tax = round(random.uniform(0.1, 0.2), 2)

            net = (shares * dps) * (1.0 - tax)
            total_expected_net += net

            portfolio_assets.append(
                {
                    "ticker": ticker,
                    "shares": shares,
                    "dividend_per_share": dps,
                    "tax_rate": tax,
                }
            )

        self.db_storage.get_portfolio_assets.return_value = portfolio_assets
        self.tax_calculator.calculate_tax.side_effect = lambda gross, rate: gross * rate

        aggregated_result = self.tracker.aggregate_portfolio_dividends(
            portfolio_id
        )

        self.assertEqual(
            aggregated_result["portfolio_id"], portfolio_id
        )
        self.assertAlmostEqual(
            aggregated_result["total_net_dividends"], total_expected_net, places=2
        )
        self.db_storage.get_portfolio_assets.assert_called_once_with(
            portfolio_id
        )

    def test_dividend_calendar_generation(self):
        owner_uuid = str(uuid.uuid4())
        random_month = random.randint(1, 12)
        random_year = random.randint(2024, 2030)

        mock_payload = f"calendar_data_{uuid.uuid4().hex}".encode()

        with patch(
            "skills.market_portfolio_dividend_tracker.requests.get"
        ) as mock_req:
            mock_resp = MagicMock()
            mock_resp.content = mock_payload
            mock_resp.status_code = 200
            mock_req.return_value = mock_resp

            calendar = self.tracker.get_dividend_calendar(
                owner_uuid, random_month, random_year
            )

            self.assertIn("calendar_entries", calendar)
            self.assertEqual(calendar["owner"], owner_uuid)
            self.assertEqual(calendar["month"], random_month)
            self.assertEqual(calendar["year"], random_year)


if __name__ == "__main__":
    unittest.main()