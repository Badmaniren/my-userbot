import unittest
import uuid
import random
import io
import os
import json
from skills.market_portfolio_stress_backtest_aggregator_v2 import (
    StressBacktestAggregatorV2,
    AggregatorError,
    aggregate_stress_backtests
)

class RealDbStorageStub:
    def __init__(self):
        self.saved_records = []

    def save_aggregation(self, record):
        self.saved_records.append(record)

class TestIntegrationStressBacktestAggregatorV2(unittest.TestCase):
    def setUp(self):
        self.db_storage = RealDbStorageStub()
        self.aggregator = StressBacktestAggregatorV2(db_storage=self.db_storage)

    def test_aggregate_stream_integration(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        rand_metric = f"var_{random.choice([95, 99])}"
        rand_value = round(random.uniform(-50000.0, -100.0), 2)

        line_data = f"{rand_portfolio_id},{rand_scenario_id},{rand_metric},{rand_value}\n"
        stream = io.BytesIO(line_data.encode('utf-8'))

        result = self.aggregator.aggregate_stream(stream)

        self.assertIn('batch_id', result)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['records_processed'], 1)

        self.assertEqual(len(self.db_storage.saved_records), 1)
        saved_record = self.db_storage.saved_records[0]
        self.assertEqual(saved_record['portfolio_id'], rand_portfolio_id)
        self.assertEqual(saved_record['scenario_id'], rand_scenario_id)
        self.assertEqual(saved_record['metric'], rand_metric)
        self.assertEqual(saved_record['value'], rand_value)

    def test_aggregate_stress_backtests_file_output(self):
        rand_portfolio_id = f"port_batch_{uuid.uuid4().hex[:6]}"
        rand_backtest_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        rand_output_path = f"test_outputs/report_{uuid.uuid4().hex}.json"

        payload = {
            "portfolio_id": rand_portfolio_id,
            "backtest_ids": rand_backtest_ids,
            "output_path": rand_output_path
        }

        try:
            report = aggregate_stress_backtests(payload)

            self.assertEqual(report["portfolio_id"], rand_portfolio_id)
            self.assertEqual(report["processed_backtests"], rand_backtest_ids)
            self.assertEqual(report["status"], "COMPLETED")

            self.assertTrue(os.path.exists(rand_output_path))
            with open(rand_output_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data["portfolio_id"], rand_portfolio_id)
            self.assertEqual(loaded_data["processed_backtests"], rand_backtest_ids)
            self.assertEqual(loaded_data["status"], "COMPLETED")
        finally:
            if os.path.exists(rand_output_path):
                os.remove(rand_output_path)
                try:
                    os.rmdir(os.path.dirname(rand_output_path))
                except OSError:
                    pass

    def test_aggregate_stream_malformed_data(self):
        bad_stream = io.BytesIO(b"invalid,csv,data\n")
        with self.assertRaises(AggregatorError):
            self.aggregator.aggregate_stream(bad_stream)

if __name__ == '__main__':
    unittest.main()