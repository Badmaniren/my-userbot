import unittest
import uuid
import random

from skills.market_portfolio_stress_stress_testing_dashboard_aggregator import (
    market_portfolio_stress_stress_testing_dashboard_aggregator,
    start_new
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressTestingDashboardAggregatorIntegration(unittest.TestCase):

    def test_start_new_validation_error(self):
        with self.assertRaises(ValueError):
            start_new()

    def test_start_new_success_flow(self):
        rand_key = f"db_{uuid.uuid4().hex}"
        payload = {
            "db_storage": rand_key
        }
        result = start_new(**payload)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "aggregated")
        self.assertIn("token", result)
        self.assertIn("target", result)
        self.assertTrue(len(result["token"]) > 0)
        self.assertTrue(len(result["target"]) > 0)

    def test_dashboard_aggregator_integration(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        unique_dashboard_id = f"dash_{uuid.uuid4().hex[:10]}"

        mc_val = random.uniform(1000.0, 50000.0)
        scenario_val = random.randint(1, 10)
        var_val = random.uniform(0.01, 0.99)

        payload = {
            "portfolio_id": unique_portfolio_id,
            "dashboard_id": unique_dashboard_id,
            "monte_carlo_data": {"simulations": mc_val},
            "scenario_matrix_data": {"matrix_id": scenario_val},
            "var_data": {"var_95": var_val},
            "include_alerts": True
        }

        response = market_portfolio_stress_stress_testing_dashboard_aggregator(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "success")

        report_id = response.get("report_id")
        dashboard_id = response.get("dashboard_id")

        self.assertIsNotNone(report_id)
        self.assertEqual(dashboard_id, unique_dashboard_id)

        stored_record = db_storage({
            "action": "get",
            "key": report_id
        })

        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), unique_portfolio_id)
        self.assertEqual(stored_record.get("dashboard_id"), unique_dashboard_id)
        self.assertEqual(stored_record.get("monte_carlo_data"), payload["monte_carlo_data"])
        self.assertEqual(stored_record.get("scenario_matrix_data"), payload["scenario_matrix_data"])
        self.assertEqual(stored_record.get("var_data"), payload["var_data"])

if __name__ == "__main__":
    unittest.main()