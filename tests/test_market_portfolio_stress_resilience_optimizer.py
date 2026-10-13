import unittest
from unittest.mock import patch
import uuid
import random

class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def test_start_new_success_integration(self):
        portfolio_id = uuid.uuid4().hex
        mock_health = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_scenario = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207') as mock_ext1, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839') as mock_ext2, \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge') as mock_bridge:

            mock_ingestor.read_stream.return_value = None
            mock_ext1.extract.return_value = None
            mock_ext2.extract.return_value = None
            mock_db.get_health_metrics.return_value = mock_health
            mock_bridge.run_simulation.return_value = mock_scenario

            from skills.market_portfolio_stress_resilience_optimizer import start_new
            res = start_new(portfolio_id)

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get('portfolio_id'), portfolio_id)
            self.assertEqual(res.get('status'), 'optimized')
            self.assertIn(list(mock_health.keys())[0], res)
            self.assertIn(list(mock_scenario.keys())[0], res)
            mock_db.get_health_metrics.assert_called_once_with(portfolio_id)
            mock_bridge.run_simulation.assert_called_once_with(portfolio_id)

    def test_start_new_missing_dependencies(self):
        portfolio_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge', None):

            from skills.market_portfolio_stress_resilience_optimizer import start_new
            res = start_new(portfolio_id)

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get('portfolio_id'), portfolio_id)
            self.assertEqual(res.get('status'), 'optimized')

    def test_market_portfolio_stress_resilience_optimizer_execution(self):
        portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": portfolio_id}

        mock_db_callable = unittest.mock.MagicMock()

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', mock_db_callable):
            from skills.market_portfolio_stress_resilience_optimizer import market_portfolio_stress_resilience_optimizer
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), portfolio_id)
            self.assertIn("resilience_score", response)
            self.assertIsInstance(response.get("resilience_score"), float)
            self.assertTrue(0.8 <= response.get("resilience_score") <= 1.0)
            
            mock_db_callable.assert_any_call(f"save_resilience:{portfolio_id}")
            mock_db_callable.assert_any_call(f"get_resilience:{portfolio_id}")

    def test_market_portfolio_stress_resilience_optimizer_no_db(self):
        portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": portfolio_id}

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None):
            from skills.market_portfolio_stress_resilience_optimizer import market_portfolio_stress_resilience_optimizer
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), portfolio_id)
            self.assertIn("resilience_score", response)

if __name__ == '__main__':
    unittest.main()