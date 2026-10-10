import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import os
import json
import tempfile

from skills.market_portfolio_stress_backtest_aggregator_v2 import (
    AggregatorError,
    StressBacktestAggregatorV2,
    aggregate_stress_backtests
)


class TestStressBacktestAggregatorV2(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.evaluator_mock = MagicMock()
        self.aggregator = StressBacktestAggregatorV2(
            db_storage=self.db_storage_mock,
            evaluator=self.evaluator_mock
        )

    def test_aggregate_stream_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_id = uuid.uuid4().hex
        metric = f"metric_{uuid.uuid4().hex[:6]}"
        val = round(random.uniform(10.0, 1000.0), 4)

        line = f"{portfolio_id},{scenario_id},{metric},{val}"
        stream = io.BytesIO(line.encode('utf-8'))

        result = self.aggregator.aggregate_stream(stream)

        self.assertIn('batch_id', result)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['records_processed'], 1)

        self.db_storage_mock.save_aggregation.assert_called_once()
        saved_record = self.db_storage_mock.save_aggregation.call_args[0][0]
        self.assertEqual(saved_record['portfolio_id'], portfolio_id)
        self.assertEqual(saved_record['scenario_id'], scenario_id)
        self.assertEqual(saved_record['metric'], metric)
        self.assertEqual(saved_record['value'], val)

    def test_aggregate_stream_empty(self):
        stream = io.BytesIO(b"")
        with self.assertRaises(AggregatorError) as ctx:
            self.aggregator.aggregate_stream(stream)
        self.assertIn("Empty stream data", str(ctx.exception))

    def test_aggregate_stream_invalid_format(self):
        bad_line = f"{uuid.uuid4().hex},{uuid.uuid4().hex}"
        stream = io.BytesIO(bad_line.encode('utf-8'))
        with self.assertRaises(AggregatorError) as ctx:
            self.aggregator.aggregate_stream(stream)
        self.assertIn("Malformed stream data", str(ctx.exception))

    def test_aggregate_stream_invalid_float(self):
        portfolio_id = uuid.uuid4().hex
        scenario_id = uuid.uuid4().hex
        metric = f"metric_{uuid.uuid4().hex[:6]}"
        bad_val = f"not_a_number_{uuid.uuid4().hex[:4]}"

        line = f"{portfolio_id},{scenario_id},{metric},{bad_val}"
        stream = io.BytesIO(line.encode('utf-8'))

        with self.assertRaises(AggregatorError) as ctx:
            self.aggregator.aggregate_stream(stream)
        self.assertIn("Malformed stream data", str(ctx.exception))

    def test_aggregate_with_evaluation(self):
        portfolio_id = uuid.uuid4().hex
        scenario_id = uuid.uuid4().hex
        metric = f"eval_metric_{uuid.uuid4().hex[:6]}"
        val = round(random.uniform(1.0, 50.0), 2)

        line = f"{portfolio_id},{scenario_id},{metric},{val}"
        stream = io.BytesIO(line.encode('utf-8'))

        eval_result_expected = {'score': random.randint(80, 100), 'passed': True}
        self.evaluator_mock.evaluate.return_value = eval_result_expected

        result = self.aggregator.aggregate_with_evaluation(stream)

        self.assertEqual(result['status'], 'SUCCESS')
        self.assertIn('evaluation', result)
        self.assertEqual(result['evaluation'], eval_result_expected)
        self.evaluator_mock.evaluate.assert_called_once()

    def test_aggregate_stress_backtests_function(self):
        portfolio_id = uuid.uuid4().hex
        backtest_ids = [uuid.uuid4().hex for _ in range(random.randint(1, 5))]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_filename = f"report_{uuid.uuid4().hex}.json"
            output_path = os.path.join(tmpdir, f"sub_{uuid.uuid4().hex[:4]}", output_filename)

            payload = {
                "portfolio_id": portfolio_id,
                "backtest_ids": backtest_ids,
                "output_path": output_path
            }

            report = aggregate_stress_backtests(payload)

            self.assertEqual(report["portfolio_id"], portfolio_id)
            self.assertEqual(report["processed_backtests"], backtest_ids)
            self.assertEqual(report["status"], "COMPLETED")

            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertEqual(data["portfolio_id"], portfolio_id)
            self.assertEqual(data["processed_backtests"], backtest_ids)

    def test_aggregate_stress_backtests_no_output(self):
        portfolio_id = uuid.uuid4().hex
        backtest_ids = [uuid.uuid4().hex]

        payload = {
            "portfolio_id": portfolio_id,
            "backtest_ids": backtest_ids
        }

        report = aggregate_stress_backtests(payload)
        self.assertEqual(report["portfolio_id"], portfolio_id)
        self.assertEqual(report["status"], "COMPLETED")


if __name__ == '__main__':
    unittest.main()