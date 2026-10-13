import unittest
import uuid
import random

from skills import market_portfolio_stress_resilience_optimizer
from skills import db_storage
from skills import market_portfolio_realtime_stream_ingestor
from skills import market_portfolio_stress_scenario_executor_bridge


class TestMarketPortfolioStressResilienceOptimizerIntegration(unittest.TestCase):

    def test_optimization_flow_without_mocks(self):
        test_portfolio_id = str(uuid.uuid4())
        payload = {
            "portfolio_id": test_portfolio_id,
            "random_seed_factor": random.randint(1, 1000000)
        }

        if hasattr(market_portfolio_realtime_stream_ingestor, 'read_stream'):
            try:
                market_portfolio_realtime_stream_ingestor.read_stream()
            except Exception:
                pass

        if hasattr(market_portfolio_stress_scenario_executor_bridge, 'run_simulation'):
            try:
                market_portfolio_stress_scenario_executor_bridge.run_simulation(test_portfolio_id)
            except Exception:
                pass

        result_start = market_portfolio_stress_resilience_optimizer.start_new(test_portfolio_id)
        
        self.assertIsInstance(result_start, dict)
        self.assertIn('portfolio_id', result_start)
        self.assertEqual(result_start['portfolio_id'], test_portfolio_id)
        self.assertEqual(result_start.get('status'), 'optimized')

        response = market_portfolio_stress_resilience_optimizer.market_portfolio_stress_resilience_optimizer(payload)

        self.assertIsInstance(response, dict)
        self.assertIn("optimized_portfolio_id", response)
        self.assertIn("resilience_score", response)
        self.assertEqual(response["optimized_portfolio_id"], test_portfolio_id)
        
        score = response["resilience_score"]
        self.assertIsInstance(score, float)
        self.assertTrue(0.8 <= score <= 1.0)

        if db_storage is not None and hasattr(db_storage, 'get_health_metrics'):
            try:
                db_storage.get_health_metrics(test_portfolio_id)
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()