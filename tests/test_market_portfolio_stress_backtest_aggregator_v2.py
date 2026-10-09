import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_backtest_aggregator_v2 import (
    StressBacktestAggregatorV2,
    AggregatorError
)


class TestStressBacktestAggregatorV2(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.evaluator = MagicMock()
        self.aggregator = StressBacktestAggregatorV2(
            db_storage=self.db_storage,
            evaluator=self.evaluator
        )
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_scenario_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_value = random.uniform(-1000.0, 1000.0)

    def test_aggregate_metrics_success(self):
        raw_stream_data = f"{self.random_portfolio_id},{self.random_scenario_id},{self.random_metric_name},{self.random_value}".encode('utf-8')
        mock_file_stream = io.BytesIO(raw_stream_data)

        with patch('skills.market_portfolio_stress_backtest_aggregator_v2.uuid.uuid4') as mock_uuid:
            expected_batch_id = uuid.uuid4()
            mock_uuid.return_value = expected_batch_id

            result = self.aggregator.aggregate_stream(mock_file_stream)

            self.assertIsInstance(result, dict)
            self.assertEqual(result['batch_id'], expected_batch_id.hex)
            self.assertEqual(result['status'], 'SUCCESS')
            self.assertEqual(result['records_processed'], 1)
            
            self.db_storage.save_aggregation.assert_called_once()
            args, _ = self.db_storage.save_aggregation.call_args
            self.assertEqual(args[0]['portfolio_id'], self.random_portfolio_id)
            self.assertEqual(args[0]['scenario_id'], self.random_scenario_id)
            self.assertEqual(args[0]['metric'], self.random_metric_name)
            self.assertEqual(args[0]['value'], self.random_value)

    def test_aggregate_metrics_corrupted_stream_raises_exception(self):
        garbage_data = ''.join(random.choices(string.ascii_letters + string.punctuation, k=50)).encode('latin1')
        mock_file_stream = io.BytesIO(garbage_data)

        with self.assertRaises(AggregatorError) as context:
            self.aggregator.aggregate_stream(mock_file_stream)

        self.assertIn("Malformed stream data", str(context.exception))
        self.db_storage.save_aggregation.assert_not_called()

    def test_aggregate_with_evaluator_integration(self):
        mock_eval_result = {
            "score": random.uniform(0.0, 100.0),
            "risk_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }
        self.evaluator.evaluate.return_value = mock_eval_result

        raw_stream_data = f"{self.random_portfolio_id},{self.random_scenario_id},{self.random_metric_name},{self.random_value}".encode('utf-8')
        mock_file_stream = io.BytesIO(raw_stream_data)

        result = self.aggregator.aggregate_with_evaluation(mock_file_stream)

        self.assertEqual(result['evaluation']['score'], mock_eval_result['score'])
        self.assertEqual(result['evaluation']['risk_level'], mock_eval_result['risk_level'])
        self.evaluator.evaluate.assert_called_once()

    def test_empty_stream_handling(self):
        mock_file_stream = io.BytesIO(b"")

        with self.assertRaises(AggregatorError):
            self.aggregator.aggregate_stream(mock_file_stream)

        self.db_storage.save_aggregation.assert_not_called()


if __name__ == '__main__':
    unittest.main()