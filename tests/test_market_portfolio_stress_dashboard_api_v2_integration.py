import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_dashboard_api_v2 import market_portfolio_stress_dashboard_api_v2_handler
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline_handler
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine_handler
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter_handler
from skills.db_storage import db_storage_handler

class TestMarketPortfolioStressDashboardApiV2Integration(unittest.TestCase):
    def test_stress_dashboard_api_end_to_end_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        shock_magnitude = round(random.uniform(-0.5, -0.1), 4)
        simulations_count = random.randint(100, 1000)
        output_format = random.choice(["json", "pdf", "html"])

        scenario_payload = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "shock_magnitude": shock_magnitude,
            "simulations": simulations_count
        }

        pipeline_res = market_portfolio_stress_scenario_pipeline_handler(scenario_payload)
        self.assertIn("status", pipeline_res)
        self.assertEqual(pipeline_res.get("scenario_id"), scenario_id)

        mc_payload = {
            "scenario_id": scenario_id,
            "simulations": simulations_count,
            "volatility_multiplier": random.uniform(1.0, 3.0)
        }
        mc_res = market_portfolio_stress_monte_carlo_engine_handler(mc_payload)
        self.assertIn("var_95", mc_res)

        report_payload = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "monte_carlo_data": mc_res,
            "format": output_format
        }
        report_res = market_portfolio_stress_reporter_handler(report_payload)
        report_path = report_res.get("file_path")
        self.assertTrue(report_path)
        self.assertTrue(os.path.exists(report_path))

        dashboard_api_payload = {
            "action": "aggregate_and_visualize",
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "report_path": report_path,
            "export_format": output_format
        }
        api_response = market_portfolio_stress_dashboard_api_v2_handler(dashboard_api_payload)

        self.assertEqual(api_response.get("portfolio_id"), portfolio_id)
        self.assertEqual(api_response.get("scenario_id"), scenario_id)
        self.assertEqual(api_response.get("status"), "success")

        db_check = db_storage_handler({"query": "get_dashboard_metric", "portfolio_id": portfolio_id})
        self.assertIsNotNone(db_check)

        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == "__main__":
    unittest.main()