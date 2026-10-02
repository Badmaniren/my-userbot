import unittest
import uuid
import os
from skills.market_portfolio_stress_dashboard_api_v2 import (
    market_portfolio_stress_dashboard_api_v2_handler,
    market_portfolio_stress_scenario_pipeline_handler
)

class TestMarketPortfolioStressDashboardApiV2Integration(unittest.TestCase):
    def test_dashboard_api_v2_pipeline_integration(self):
        random_portfolio_id = f"port_{uuid.uuid4()}"
        random_scenario_id = f"scen_{uuid.uuid4()}"
        random_report_path = f"/tmp/report_{uuid.uuid4()}.pdf"
        random_export_format = "pdf"

        scenario_payload = {
            "scenario_id": random_scenario_id
        }
        scenario_result = market_portfolio_stress_scenario_pipeline_handler(scenario_payload)
        self.assertEqual(scenario_result.get("status"), "success")
        self.assertEqual(scenario_result.get("scenario_id"), random_scenario_id)

        dashboard_payload = {
            "portfolio_id": random_portfolio_id,
            "scenario_id": random_scenario_id,
            "report_path": random_report_path,
            "export_format": random_export_format
        }
        
        dashboard_result = market_portfolio_stress_dashboard_api_v2_handler(dashboard_payload)

        self.assertEqual(dashboard_result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(dashboard_result.get("scenario_id"), random_scenario_id)
        self.assertEqual(dashboard_result.get("status"), "success")
        self.assertEqual(dashboard_result.get("report_path"), random_report_path)
        self.assertEqual(dashboard_result.get("export_format"), random_export_format)

if __name__ == "__main__":
    unittest.main()