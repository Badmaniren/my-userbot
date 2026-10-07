import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_stress_testing_dashboard_aggregator import (
    start_new,
    market_portfolio_stress_stress_testing_dashboard_aggregator
)

class TestMarketPortfolioStressTestingDashboardAggregator(unittest.TestCase):

    def test_start_new_validation_error(self):
        with self.assertRaises(ValueError):
            start_new()
        with self.assertRaises(ValueError):
            start_new(random_key=uuid.uuid4().hex)

    def test_start_new_stream_reading(self):
        rand_bytes = bytes(random.choices(range(256), k=32))
        mock_stream = io.BytesIO(rand_bytes)
        tool_key = f"extractor_tool_{random.randint(100000000, 999999999)}"
        payload = {
            "db_storage": lambda x: x,
            tool_key: mock_stream
        }
        res = start_new(**payload)
        self.assertIn("stream_checked", res)
        self.assertTrue(res["stream_checked"])
        self.assertEqual(res["read_val"], rand_bytes)

    def test_start_new_success_flow(self):
        payload = {
            "db_storage": lambda x: x,
            str(uuid.uuid4()): random.randint(1, 100)
        }
        res = start_new(**payload)
        self.assertIn("status", res)
        self.assertEqual(res["status"], "aggregated")
        self.assertIn("token", res)
        self.assertIn("target", res)

    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.db_storage")
    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.market_portfolio_stress_reporter")
    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.market_portfolio_alert_dispatcher")
    def test_dashboard_aggregator_integration(self, mock_alert, mock_reporter, mock_db):
        rand_portfolio = f"port_{uuid.uuid4().hex[:6]}"
        rand_dashboard = f"dash_{uuid.uuid4().hex[:6]}"
        mc_data = {"simulation": random.uniform(0, 1)}
        scenario_data = {"matrix": random.randint(1, 10)}
        var_data = {"var_95": random.uniform(-10, 0)}

        payload = {
            "portfolio_id": rand_portfolio,
            "dashboard_id": rand_dashboard,
            "monte_carlo_data": mc_data,
            "scenario_matrix_data": scenario_data,
            "var_data": var_data,
            "include_alerts": True
        }

        res = market_portfolio_stress_stress_testing_dashboard_aggregator(payload)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["dashboard_id"], rand_dashboard)
        self.assertTrue(res["report_id"].startswith("rep_"))

        mock_db.assert_called_once()
        db_arg = mock_db.call_args[0][0]
        self.assertEqual(db_arg["action"], "set")
        self.assertEqual(db_arg["value"]["portfolio_id"], rand_portfolio)
        self.assertEqual(db_arg["value"]["monte_carlo_data"], mc_data)

        mock_reporter.assert_called_once()
        mock_alert.assert_called_once()
        alert_arg = mock_alert.call_args[0][0]
        self.assertEqual(alert_arg["source"], "dashboard_aggregator")
        self.assertEqual(alert_arg["portfolio_id"], rand_portfolio)

    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.db_storage")
    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.market_portfolio_stress_reporter")
    @patch("skills.market_portfolio_stress_stress_testing_dashboard_aggregator.market_portfolio_alert_dispatcher")
    def test_dashboard_aggregator_no_alerts(self, mock_alert, mock_reporter, mock_db):
        payload = {
            "portfolio_id": f"port_{uuid.uuid4().hex[:4]}",
            "include_alerts": False
        }

        res = market_portfolio_stress_stress_testing_dashboard_aggregator(payload)
        self.assertEqual(res["status"], "success")
        mock_alert.assert_not_called()
        mock_reporter.assert_called_once()
        mock_db.assert_called_once()

if __name__ == "__main__":
    unittest.main()