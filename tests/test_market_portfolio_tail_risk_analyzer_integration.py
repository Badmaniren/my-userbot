import unittest
import uuid
import random
import os
from skills.market_portfolio_tail_risk_analyzer import market_portfolio_tail_risk_analyzer
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class TestMarketPortfolioTailRiskAnalyzerIntegration(unittest.TestCase):
    def test_tail_risk_analyzer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(1000, 5000)
        confidence_level = round(random.uniform(0.95, 0.99), 2)

        monte_carlo_input = {
            "portfolio_id": portfolio_id,
            "runs": simulation_runs,
            "horizon_days": random.randint(10, 30),
            "initial_value": round(random.uniform(50000.0, 500000.0), 2)
        }

        mc_engine_result = market_portfolio_stress_monte_carlo_engine(monte_carlo_input)

        self.assertIsInstance(mc_engine_result, dict)
        self.assertIn("simulation_id", mc_engine_result)

        analyzer_payload = {
            "portfolio_id": portfolio_id,
            "simulation_id": mc_engine_result["simulation_id"],
            "confidence_level": confidence_level
        }

        tail_risk_result = market_portfolio_tail_risk_analyzer(analyzer_payload)

        self.assertIsInstance(tail_risk_result, dict)
        self.assertEqual(tail_risk_result.get("portfolio_id"), portfolio_id)
        self.assertIn("expected_shortfall", tail_risk_result)
        self.assertIn("cvar", tail_risk_result)

        stored_record = db_storage({
            "action": "get",
            "table": "tail_risk_metrics",
            "portfolio_id": portfolio_id
        })

        self.assertIsInstance(stored_record, dict)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)
        self.assertIn("expected_shortfall", stored_record)

if __name__ == "__main__":
    unittest.main()