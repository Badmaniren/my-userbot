import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_dashboard_bridge import (
    market_portfolio_stress_audit_dashboard_bridge,
    db_storage,
    market_portfolio_collector_agent,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_stress_monte_carlo_engine
)

class TestMarketPortfolioStressAuditDashboardBridgeIntegration(unittest.TestCase):
    def test_dashboard_bridge_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        test_asset_count = random.randint(3, 10)
        risk_factor = round(random.uniform(0.01, 0.5), 4)

        raw_market_data = {
            "portfolio_id": portfolio_id,
            "assets_count": test_asset_count,
            "volatility_index": risk_factor,
            "timestamp": uuid.uuid1().hex
        }

        collected_data = market_portfolio_collector_agent(raw_market_data)
        self.assertIsNotNone(collected_data, "Collector agent failed to gather data")

        scenario_result = market_portfolio_stress_scenario_pipeline(collected_data)
        self.assertIsNotNone(scenario_result, "Stress scenario pipeline execution failed")

        monte_carlo_metrics = market_portfolio_stress_monte_carlo_engine(scenario_result)
        self.assertIsNotNone(monte_carlo_metrics, "Monte Carlo engine failed to compute metrics")

        dashboard_payload = {
            "portfolio_id": portfolio_id,
            "monte_carlo": monte_carlo_metrics,
            "scenario": scenario_result,
            "integrity_check": True
        }

        bridge_output = market_portfolio_stress_audit_dashboard_bridge(dashboard_payload)
        self.assertIsInstance(bridge_output, dict, "Bridge output must be a dictionary")
        self.assertEqual(bridge_output.get("portfolio_id"), portfolio_id, "Portfolio ID mismatch in bridge output")
        self.assertIn("dashboard_status", bridge_output, "Dashboard status metric missing")
        self.assertEqual(bridge_output["dashboard_status"], "SUCCESS")

        saved_record = db_storage.get(portfolio_id)
        self.assertIsNotNone(saved_record, "Data was not successfully committed to db_storage")
        self.assertEqual(saved_record["portfolio_id"], portfolio_id)

if __name__ == "__main__":
    unittest.main()