import unittest
import uuid
import random
from skills.market_portfolio_stress_dashboard_api import market_portfolio_stress_dashboard_api, start_new
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter


class TestMarketPortfolioStressDashboardApiIntegration(unittest.TestCase):

    def test_aggregate_dashboard_metrics_and_start_new(self):
        test_portfolio_id = str(uuid.uuid4())
        test_report_id = str(uuid.uuid4())

        dashboard_api = market_portfolio_stress_dashboard_api()
        query = {
            "portfolio_id": test_portfolio_id,
            "report_id": test_report_id
        }

        result = dashboard_api.aggregate_dashboard_metrics(query)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), test_portfolio_id)
        self.assertEqual(result.get("report_id"), test_report_id)
        self.assertIn("aggregated_metrics", result)
        self.assertEqual(result["aggregated_metrics"].get("status"), "aggregated")

        sim = market_portfolio_scenario_simulator()
        db = db_storage()

        dependencies = {
            "market_portfolio_scenario_simulator": sim,
            "db_storage": db,
            "market_portfolio_api_gateway": None,
            "market_anomaly_detector": None
        }

        start_result = start_new(dependencies)
        self.assertIsInstance(start_result, dict)
        self.assertEqual(start_result.get("status"), "success")


if __name__ == "__main__":
    unittest.main()