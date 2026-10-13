import unittest
from unittest.mock import patch
import uuid
import random

from skills import market_portfolio_stress_resilience_optimizer as optimizer


class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def test_start_new_success_execution(self):
        portfolio_id = str(uuid.uuid4())
        mock_health_metrics = {'health_score': round(random.uniform(0.5, 1.0), 2)}
        mock_scenario_res = {'scenario_impact': round(random.uniform(-0.5, 0.0), 2)}

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207') as mock_ext1, \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839') as mock_ext2, \
             patch('skills.market_portfolio_stress_resilience_optimizer.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge') as mock_bridge:

            mock_ingestor.read_stream.return_value = None
            mock_ext1.extract.return_value = None
            mock_ext2.extract.return_value = None
            mock_db.get_health_metrics.return_value = mock_health_metrics
            mock_bridge.run_simulation.return_value = mock_scenario_res

            result = optimizer.start_new(portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')
            self.assertEqual(result.get('health_score'), mock_health_metrics['health_score'])
            self.assertEqual(result.get('scenario_impact'), mock_scenario_res['scenario_impact'])

            mock_ingestor.read_stream.assert_called_once()
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

            result = optimizer.start_new(portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get('portfolio_id'), portfolio_id)
            self.assertEqual(result.get('status'), 'optimized')

    def tf_market_portfolio_stress_resilience_optimizer_payload(self):
        pass

    def test_market_portfolio_stress_resilience_optimizer_execution(self):
        portfolio_id = str(uuid.uuid4())
        payload = {"portfolio_id": portfolio_id}

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage') as mock_db:
            mock_db.return_value = None

            response = optimizer.market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), portfolio_id)
            self.assertIn("resilience_score", response)
            self.assertIsInstance(response.get("resilience_score"), float)
            self.assertTrue(0.8 <= response.get("resilience_score") <= 1.0)

            self.assertEqual(mock_db.call_count, 2)
            mock_db.assert_any_call(f"save_resilience:{portfolio_id}")
            mock_db.assert_any_call(f"get_resilience:{portfolio_id}")

    def test_market_portfolio_stress_resilience_optimizer_no_db(self):
        portfolio_id = str(uuid.uuid4())
        payload = {"portfolio_id": portfolio_id}

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', None):
            response = optimizer.market_portfolio_stress_resilience_optimizer(payload)

            self.assertIsInstance(response, dict)
            self.assertEqual(response.get("optimized_portfolio_id"), portfolio_id)
            self.assertIn("resilience_score", response)


if __name__ == '__main__':
    unittest.main()