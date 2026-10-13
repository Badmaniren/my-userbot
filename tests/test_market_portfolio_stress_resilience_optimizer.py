import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import sys
import types

if 'skills' not in sys.modules:
    skills_mock = types.ModuleType('skills')
    sys.modules['skills'] = skills_mock

from skills.market_portfolio_stress_resilience_optimizer import start_new, market_portfolio_stress_resilience_optimizer

class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def test_start_new_full_workflow(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_health_key = uuid.uuid4().hex
        rand_health_val = uuid.uuid4().hex
        rand_scenario_key = uuid.uuid4().hex
        rand_scenario_val = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor') as mock_stream, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207') as mock_ext1, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839') as mock_ext2, \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge') as mock_scenario:

            mock_stream.read_stream = MagicMock()
            mock_ext1.extract = MagicMock()
            mock_ext2.extract = MagicMock()
            mock_db.get_health_metrics.return_value = {rand_health_key: rand_health_val}
            mock_scenario.run_simulation.return_value = {rand_scenario_key: rand_scenario_val}

            result = start_new(rand_portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), rand_portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')
            self.assertEqual(result.get(rand_health_key), rand_health_val)
            self.assertEqual(result.get(rand_scenario_key), rand_scenario_val)

            mock_stream.read_stream.assert_called_once()
            mock_ext1.extract.assert_called_once()
            mock_ext2.extract.assert_called_once()
            mock_db.get_health_metrics.assert_called_once_with(rand_portfolio_id)
            mock_scenario.run_simulation.assert_called_once_with(rand_portfolio_id)

    def test_start_new_missing_dependencies(self):
        rand_portfolio_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None), \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge', None):

            result = start_new(rand_portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), rand_portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')

    def test_market_portfolio_stress_resilience_optimizer_execution(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio_id}
        
        mock_db_callable = MagicMock()

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', mock_db_callable):
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), rand_portfolio_id)
            self.assertIn("resilience_score", response)
            
            score = response.get("resilience_score")
            self.assertIsInstance(score, float)
            self.assertTrue(0.8 <= score <= 1.0)

            mock_db_callable.assert_any_call(f"save_resilience:{rand_portfolio_id}")
            mock_db_callable.assert_any_call(f"get_resilience:{rand_portfolio_id}")
            self.assertEqual(mock_db_callable.call_count, 2)

    def test_market_portfolio_stress_resilience_optimizer_no_db(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio_id}

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None):
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), rand_portfolio_id)
            self.assertIn("resilience_score", response)
            self.assertTrue(0.8 <= response.get("resilience_score") <= 1.0)

if __name__ == '__main__':
    unittest.main()