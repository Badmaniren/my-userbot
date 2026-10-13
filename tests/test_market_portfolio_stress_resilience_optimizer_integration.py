import unittest
import uuid
import random

from skills.market_portfolio_stress_resilience_optimizer import start_new, market_portfolio_stress_resilience_optimizer


class TestMarketPortfolioStressResilienceOptimizerIntegration(unittest.TestCase):

    def test_start_new_integration_flow(self):
        random_portfolio_id = str(uuid.uuid4())
        
        result = start_new(random_portfolio_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn('portfolio_id', result)
        self.assertEqual(result['portfolio_id'], random_portfolio_id)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'optimized')

    def test_market_portfolio_stress_resilience_optimizer_payload(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        payload = {
            "portfolio_id": random_portfolio_id,
            "extra_param": random.randint(100, 999)
        }

        response = market_portfolio_stress_resilience_optimizer(payload)

        self.assertIsInstance(response, dict)
        self.assertIn("optimized_portfolio_id", response)
        self.assertEqual(response["optimized_portfolio_id"], random_portfolio_id)
        self.assertIn("resilience_score", response)
        self.assertIsInstance(response["resilience_score"], float)
        self.assertTrue(0.8 <= response["resilience_score"] <= 1.0)


if __name__ == '__main__':
    unittest.main()