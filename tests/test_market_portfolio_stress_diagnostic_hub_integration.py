import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_diagnostic_hub import market_portfolio_stress_diagnostic_hub
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_stress_resilience_optimizer import market_portfolio_stress_resilience_optimizer

class TestMarketPortfolioStressDiagnosticHubIntegration(unittest.TestCase):

    def test_stress_diagnostic_hub_end_to_end_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 1000000.0), 2)
        stress_shock_pct = round(random.uniform(-0.40, -0.10), 4)

        collector_payload = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "assets": ["AAPL", "MSFT", "GOOGL", "BTC"],
            "weights": [0.3, 0.3, 0.2, 0.2]
        }
        collected_data = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(collected_data)

        simulation_config = {
            "portfolio_id": portfolio_id,
            "shock_pct": stress_shock_pct,
            "monte_carlo_runs": random.randint(100, 1000)
        }
        simulation_result = market_portfolio_scenario_simulator(simulation_config)
        self.assertIn("scenario_id", simulation_result)

        diagnostic_payload = {
            "portfolio_id": portfolio_id,
            "simulation_data": simulation_result,
            "diagnostic_mode": "DEEP_FAIL_METRICS_ANALYSIS"
        }
        diagnostic_report = market_portfolio_stress_diagnostic_hub(diagnostic_payload)
        self.assertIn("diagnostic_report_id", diagnostic_report)

        report_id = diagnostic_report["diagnostic_report_id"]

        reporter_output = market_portfolio_stress_reporter({
            "report_id": report_id,
            "portfolio_id": portfolio_id,
            "data": diagnostic_report
        })
        self.assertTrue(reporter_output.get("rendered", False))

        optimizer_payload = {
            "portfolio_id": portfolio_id,
            "diagnostic_report_id": report_id,
            "target_resilience_score": round(random.uniform(0.80, 0.99), 2)
        }
        recovery_plan = market_portfolio_stress_resilience_optimizer(optimizer_payload)
        self.assertIn("recovery_actions", recovery_plan)
        self.assertGreater(len(recovery_plan["recovery_actions"]), 0)

        db_record = db_storage({
            "action": "SELECT",
            "table": "stress_diagnostic_logs",
            "filter": {"portfolio_id": portfolio_id}
        })
        self.assertIsInstance(db_record, list)

if __name__ == "__main__":
    unittest.main()