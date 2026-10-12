import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

from skills.market_portfolio_stress_resilience_optimizer import start_new, market_portfolio_stress_resilience_optimizer


class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def test_start_new_success_execution(self):
        portfolio_id = str(uuid.uuid4())
        rand_health_key = str(uuid.uuid4())
        rand_health_val = random.randint(100, 999)
        rand_scenario_key = str(uuid.uuid4())
        rand_scenario_val = random.randint(1000, 9999)

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor') as mock_stream, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207') as mock_ext1, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839') as mock_ext2, \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge') as mock_bridge:

            mock_stream.read_stream.return_value = True
            mock_ext1.extract.return_value = True
            mock_ext2.extract.return_value = True
            mock_db.get_health_metrics.return_value = {rand_health_key: rand_health_val}
            mock_bridge.run_simulation.return_value = {rand_scenario_key: rand_scenario_val}

            result = start_new(portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')
            self.assertEqual(result.get(rand_health_key), rand_health_val)
            self.assertEqual(result.get(rand_scenario_key), rand_scenario_val)

            mock_stream.read_stream.assert_called_once()
            mock_ext1.extract.assert_called_once()
            mock_ext2.extract.assert_called_once()
            mock_db.get_health_metrics.assert_called_once_with(portfolio_id)
            mock_bridge.run_simulation.assert_called_once_with(portfolio_id)

    def test_start_new_missing_dependencies(self):
        portfolio_id = str(uuid.uuid4())

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge', None):

            result = start_new(portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')

    def test_market_portfolio_stress_resilience_optimizer_execution(self):
        portfolio_id = str(uuid.uuid4())
        payload = {"portfolio_id": portfolio_id}

        mock_db_storage = MagicMock()

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', mock_db_storage):
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), portfolio_id)
            self.assertIn("resilience_score", response)
            self.assertIsInstance(response.get("resilience_score"), float)
            self.assertTrue(0.8 <= response.get("resilience_score") <= 1.0)

            mock_db_storage.assert_any_call(f"save_resilience:{portfolio_id}")
            mock_db_storage.assert_any_call(f"get_resilience:{portfolio_id}")


if __name__ == '__main__':
    unittest.main()