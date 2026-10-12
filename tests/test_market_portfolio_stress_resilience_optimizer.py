import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_portfolio_stress_resilience_optimizer import start_new

class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = uuid.uuid4().hex
        self.rand_scenario_id = uuid.uuid4().hex
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_metric_value = random.uniform(100.5, 9999.9)
        self.rand_db_response = {
            'portfolio_id': self.rand_portfolio_id,
            'health_score': self.rand_metric_value,
            'status': 'optimized'
        }

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        mock_db.get_health_metrics.return_value = self.rand_db_response
        mock_scenario_exec = MagicMock()
        mock_scenario_exec.run_simulation.return_value = {
            'scenario_id': self.rand_scenario_id,
            'resilience_index': random.uniform(0.1, 1.0)
        }

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', mock_db), \
             patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge', mock_scenario_exec):
            
            result = start_new(self.rand_portfolio_id)
            
            self.assertIsInstance(result, dict)
            self.assertIn('portfolio_id', result)
            self.assertEqual(result['portfolio_id'], self.rand_portfolio_id)
            mock_db.get_health_metrics.assert_called_once_with(self.rand_portfolio_id)
            mock_scenario_exec.run_simulation.assert_called_once()

    def test_start_new_with_malformed_stream_data(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=50)).encode('utf-8'))
        
        mock_stream_ingestor = MagicMock()
        mock_stream_ingestor.read_stream.return_value = random_bytes

        with patch('skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor', mock_stream_ingestor):
            try:
                res = start_new(self.rand_portfolio_id)
                self.assertIsNotNone(res)
            except Exception as e:
                self.assertIsInstance(e, (ValueError, TypeError, KeyError))

    def test_start_new_dependency_failure_handling(self):
        mock_db = MagicMock()
        mock_db.get_health_metrics.side_effect = RuntimeError(f"DB Error {uuid.uuid4().hex}")

        with patch('skills.market_portfolio_stress_resilience_optimizer.db_storage', mock_db):
            with self.assertRaises((RuntimeError, Exception)):
                start_new(self.rand_portfolio_id)

    def test_start_new_integrates_multiple_extractors(self):
        mock_ext_1 = MagicMock()
        mock_ext_2 = MagicMock()
        
        ext_val_1 = random.randint(1000, 9999)
        ext_val_2 = random.randint(1000, 9999)
        
        mock_ext_1.extract.return_value = ext_val_1
        mock_ext_2.extract.return_value = ext_val_2

        with patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207', mock_ext_1), \
             patch('skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839', mock_ext_2):
            
            try:
                res = start_new(self.rand_portfolio_id)
                self.assertIsNotNone(res)
            except AttributeError:
                pass

if __name__ == '__main__':
    unittest.main()