import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import requests

from skills.market_portfolio_tax_dividend_engine import MarketPortfolioTaxDividendEngine

class TestMarketPortfolioTaxDividendEngine(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.dividend_tracker = MagicMock()
        self.tax_calculator = MagicMock()
        self.integration_hub = MagicMock()

        self.engine = MarketPortfolioTaxDividendEngine(
            db_storage=self.db_storage,
            market_portfolio_dividend_tracker=self.dividend_tracker,
            market_portfolio_tax_calculator=self.tax_calculator,
            market_portfolio_integration_hub=self.integration_hub
        )

        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.db_conn_string = f"postgresql://user:pass@{uuid.uuid4().hex}:5432/db"

    def test_aggregate_tax_and_dividends_with_db_conn(self):
        rand_divs = round(random.uniform(100.0, 5000.0), 2)
        rand_tax = round(random.uniform(10.0, 500.0), 2)

        self.dividend_tracker.get_portfolio_dividends.return_value = {"total_dividends": rand_divs}
        self.tax_calculator.get_calculated_tax.return_value = {"total_tax": rand_tax}

        res = self.engine.aggregate_tax_and_dividends(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            db_conn_string=self.db_conn_string
        )

        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["total_dividends"], rand_divs)
        self.assertEqual(res["total_tax"], rand_tax)
        self.dividend_tracker.get_portfolio_dividends.assert_called_once_with(self.portfolio_id)
        self.tax_calculator.get_calculated_tax.assert_called_once_with(self.portfolio_id)

    def test_aggregate_tax_and_dividends_standard(self):
        rand_divs = round(random.uniform(1000.0, 10000.0), 2)
        rand_tax = round(random.uniform(100.0, 1500.0), 2)

        self.dividend_tracker.fetch_portfolio_dividends.return_value = {"total_dividends": rand_divs, "items": []}
        self.tax_calculator.calculate_liability.return_value = {"total_tax_due": rand_tax, "breakdown": []}

        res = self.engine.aggregate_tax_and_dividends(portfolio_id=self.portfolio_id)

        expected_net = round(rand_divs - rand_tax, 2)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["net_income"], expected_net)
        self.db_storage.save_aggregation_audit.assert_called_once()

    def test_verify_consistency_consistent(self):
        rand_basis = round(random.uniform(5000.0, 50000.0), 2)
        self.dividend_tracker.get_tax_basis_sum.return_value = rand_basis
        self.tax_calculator.get_declared_basis_sum.return_value = rand_basis

        res = self.engine.verify_consistency(self.portfolio_id)

        self.assertTrue(res["is_consistent"])
        self.assertEqual(res["tracker_basis"], rand_basis)
        self.assertEqual(res["calculator_basis"], rand_basis)
        self.assertEqual(res["discrepancy"], 0.0)
        self.assertIsInstance(res["incident_id"], str)

    def test_verify_consistency_inconsistent(self):
        basis_1 = round(random.uniform(1000.0, 5000.0), 2)
        basis_2 = round(basis_1 + random.uniform(10.0, 500.0), 2)
        self.dividend_tracker.get_tax_basis_sum.return_value = basis_1
        self.tax_calculator.get_declared_basis_sum.return_value = basis_2

        res = self.engine.verify_consistency(self.portfolio_id)

        self.assertFalse(res["is_consistent"])
        self.assertEqual(res["tracker_basis"], basis_1)
        self.assertEqual(res["calculator_basis"], basis_2)
        self.assertEqual(res["discrepancy"], round(abs(basis_1 - basis_2), 2))

    def test_export_audit_stream(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.com/webhook"
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)
        self.db_storage.get_audit_log_stream.return_value = mock_stream

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            success = self.engine.export_audit_stream(rand_endpoint)

            self.assertTrue(success)
            mock_post.assert_called_once_with(rand_endpoint, data=random_bytes)

    def test_process_market_anomaly_event(self):
        ticker = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        multiplier = round(random.uniform(1.1, 3.5), 2)
        anomaly_id = str(uuid.uuid4())

        payload = {
            "ticker": ticker,
            "impact_multiplier": multiplier,
            "anomaly_id": anomaly_id
        }

        res = self.engine.process_market_anomaly_event(payload)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["anomaly_id"], anomaly_id)
        self.tax_calculator.apply_multiplier.assert_called_once_with(ticker, multiplier)
        self.integration_hub.broadcast_event.assert_called_once_with(payload)