import unittest
import uuid
import random

from skills.market_portfolio_stress_resilience_guard import market_portfolio_stress_resilience_guard, start_new
from skills.db_storage import db_storage


class TestMarketPortfolioStressResilienceGuardIntegration(unittest.TestCase):

    def test_resilience_guard_integration_secure(self):
        portfolio_id = str(uuid.uuid4())
        random_val = random.randint(1, 1000)
        
        simulation_metrics = [
            {"name": "alpha", "value": random_val},
            {"name": "beta", "value": random_val + 50}
        ]

        result = market_portfolio_stress_resilience_guard(portfolio_id, simulation_metrics)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["resilience_status"], "SECURE")
        self.assertEqual(result["metrics_count"], 2)

        stored_data = db_storage(action="get", key=f"resilience_{portfolio_id}")
        self.assertEqual(stored_data, result)

    def test_resilience_guard_integration_vulnerable(self):
        portfolio_id = str(uuid.uuid4())
        negative_val = -random.randint(1, 100)
        
        simulation_metrics = [
            {"name": "drawdown", "value": negative_val},
            {"name": "stability", "value": 10}
        ]

        result = market_portfolio_stress_resilience_guard(portfolio_id, simulation_metrics)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["resilience_status"], "VULNERABLE")
        self.assertEqual(result["metrics_count"], 2)

        stored_data = db_storage(action="get", key=f"resilience_{portfolio_id}")
        self.assertEqual(stored_data["resilience_status"], "VULNERABLE")

    def test_start_new_integration_pipeline_failure(self):
        reason_msg = f"failed_test_{uuid.uuid4()}"

        class DummyPipeline:
            def evaluate(self):
                return {"status": "FAILED", "reason": reason_msg}

        dependencies = {
            "market_portfolio_stress_scenario_pipeline": DummyPipeline()
        }

        with self.assertRaises(ValueError) as ctx:
            start_new(dependencies, seed=random.randint(0, 100))
        
        self.assertIn(reason_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()