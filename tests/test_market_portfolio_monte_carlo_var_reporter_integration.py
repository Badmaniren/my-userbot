import unittest
import uuid
import random
import os
from skills.market_portfolio_monte_carlo_var_reporter import (
    market_portfolio_monte_carlo_var_reporter
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.db_storage import db_storage

class TestMarketPortfolioMonteCarloVarReporterIntegration(unittest.TestCase):
    def test_var_reporter_end_to_end_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.90, 0.99), 4)

        engine_input = {
            "portfolio_id": portfolio_id,
            "runs": simulation_runs,
            "confidence": confidence_level
        }

        engine_result = market_portfolio_stress_monte_carlo_engine(engine_input)
        self.assertIn("simulation_id", engine_result)
        simulation_id = engine_result["simulation_id"]

        reporter_input = {
            "simulation_id": simulation_id,
            "portfolio_id": portfolio_id,
            "format": "json"
        }

        report_result = market_portfolio_monte_carlo_var_reporter(reporter_input)

        self.assertIsInstance(report_result, dict)
        self.assertEqual(report_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(report_result.get("simulation_id"), simulation_id)
        self.assertIn("var_value", report_result)
        self.assertIn("expected_shortfall", report_result)

        stored_record = db_storage({
            "action": "get",
            "table": "monte_carlo_var_reports",
            "portfolio_id": portfolio_id
        })
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("simulation_id"), simulation_id)

if __name__ == "__main__":
    unittest.main()