import unittest
import uuid
import random

from skills import market_portfolio_stress_resilience_optimizer
from skills import db_storage
from skills import market_portfolio_realtime_stream_ingestor
from skills import market_portfolio_stress_scenario_executor_bridge


class TestMarketPortfolioStressResilienceOptimizerIntegration(unittest.TestCase):

    def test_start_new_and_optimizer_integration(self):
        test_portfolio_id = str(uuid.uuid4())
        
        if db_storage is not None and hasattr(db_storage, 'save_health_metrics'):
            db_storage.save_health_metrics(test_portfolio_id, {"health_score": random.uniform(0.5, 1.0)})

        start_result = market_portfolio_stress_resilience_optimizer.start_new(test_portfolio_id)
        
        self.assertIsInstance(start_result, dict)
        self.assertIn('portfolio_id', start_result)
        self.assertEqual(start_result['portfolio_id'], test_portfolio_id)
        self.assertIn('status', start_result)
        self.assertEqual(start_result['status'], 'optimized')

        payload = {
            "portfolio_id": test_portfolio_id,
            "random_seed_factor": random.randint(1, 1000)
        }

        optimizer_result = market_portfolio_stress_resilience_optimizer.market_portfolio_stress_resilience_optimizer(payload)

        self.assertIsInstance(optimizer_result, dict)
        self.assertIn('optimized_portfolio_id', optimizer_result)
        self.assertEqual(optimizer_result['optimized_portfolio_id'], test_portfolio_id)
        self.assertIn('resilience_score', optimizer_result)
        
        score = optimizer_result['resilience_score']
        self.assertIsInstance(score, float)
        self.assertTrue(0.8 <= score <= 1.0)


if __name__ == '__main__':
    unittest.main()