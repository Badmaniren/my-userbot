import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_stress_resilience_guard import start_new, market_portfolio_stress_resilience_guard


class TestMarketPortfolioStressResilienceGuard(unittest.TestCase):

    def test_start_new_with_seed(self):
        rand_seed = random.randint(1, 100000)
        dependencies = {}
        res = start_new(dependencies, seed=rand_seed)
        self.assertIsNone(res)

    def test_start_new_pipeline_fails(self):
        rand_reason = f"error_{uuid.uuid4().hex}"
        mock_pipeline = MagicMock()
        mock_pipeline.evaluate.return_value = {"status": "FAILED", "reason": rand_reason}
        
        dependencies = {
            "market_portfolio_stress_scenario_pipeline": mock_pipeline
        }

        with self.assertRaises(ValueError) as ctx:
            start_new(dependencies)
        
        self.assertIn(rand_reason, str(ctx.exception))

    def test_start_new_pipeline_fails_default_reason(self):
        mock_pipeline = MagicMock()
        mock_pipeline.evaluate.return_value = {"status": "FAILED"}
        
        dependencies = {
            "market_portfolio_stress_scenario_pipeline": mock_pipeline
        }

        with self.assertRaises(ValueError) as ctx:
            start_new(dependencies)
        
        self.assertIn("validation_failed", str(ctx.exception))

    def test_start_new_mc_engine_success(self):
        rand_result = {"simulated_value": random.uniform(100.0, 1000.0), "uuid": uuid.uuid4().hex}
        mock_mc_engine = MagicMock()
        mock_mc_engine.run_simulation.return_value = rand_result
        
        dependencies = {
            "market_portfolio_stress_monte_carlo_engine": mock_mc_engine
        }

        res = start_new(dependencies)
        self.assertEqual(res, rand_result)

    def test_start_new_no_matching_actions(self):
        mock_pipeline = MagicMock()
        mock_pipeline.evaluate.return_value = {"status": "SUCCESS"}
        
        mock_mc_engine = MagicMock()
        mock_mc_engine.run_simulation.return_value = None

        dependencies = {
            "market_portfolio_stress_scenario_pipeline": mock_pipeline,
            "market_portfolio_stress_monte_carlo_engine": mock_mc_engine
        }

        res = start_new(dependencies)
        self.assertIsNone(res)

    def test_market_portfolio_stress_resilience_guard_secure(self):
        rand_portfolio_id = uuid.uuid4().hex
        metrics = [
            {"value": random.uniform(1.0, 100.0)},
            {"value": random.uniform(101.0, 500.0)}
        ]

        with patch("skills.market_portfolio_stress_resilience_guard.db_storage") as mock_db:
            result = market_portfolio_stress_resilience_guard(rand_portfolio_id, metrics)
            
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["resilience_status"], "SECURE")
            self.assertEqual(result["metrics_count"], len(metrics))
            mock_db.assert_called_once()

    def test_market_portfolio_stress_resilience_guard_vulnerable(self):
        rand_portfolio_id = uuid.uuid4().hex
        metrics = [
            {"value": random.uniform(1.0, 100.0)},
            {"value": random.uniform(-500.0, -1.0)}
        ]

        with patch("skills.market_portfolio_stress_resilience_guard.db_storage") as mock_db:
            result = market_portfolio_stress_resilience_guard(rand_portfolio_id, metrics)
            
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["resilience_status"], "VULNERABLE")
            self.assertEqual(result["metrics_count"], len(metrics))
            mock_db.assert_called_once()


if __name__ == "__main__":
    unittest.main()