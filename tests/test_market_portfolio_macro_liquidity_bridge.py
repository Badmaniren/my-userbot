import unittest
from unittest.mock import MagicMock, patch
import uuid
import io
import random
import string

from skills.market_portfolio_macro_liquidity_bridge import MacroLiquidityBridge

class TestMarketPortfolioMacroLiquidityBridge(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.liquidity_analyzer_mock = MagicMock()
        self.bridge = MacroLiquidityBridge(
            db_storage=self.db_storage_mock,
            liquidity_analyzer=self.liquidity_analyzer_mock
        )

    def test_process_macro_event_success(self):
        event_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(10.0, 1000.0)
        stream_content = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        raw_stream = io.BytesIO(stream_content)

        payload = {
            "metric": metric_name,
            "value": metric_value,
            "raw_stream": raw_stream
        }

        expected_score = random.uniform(0.1, 1.0)
        expected_status = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.liquidity_analyzer_mock.evaluate_liquidity.return_value = {
            "score": expected_score,
            "status": expected_status
        }

        expected_db_key = uuid.uuid4().hex
        self.db_storage_mock.store_macro_metric.return_value = expected_db_key

        result = self.bridge.process_macro_event(event_id=event_id, payload=payload)

        self.assertIn("trace_id", result)
        self.assertEqual(result["event_id"], event_id)
        self.assertEqual(result["db_key"], expected_db_key)
        self.assertEqual(result["evaluation"]["score"], expected_score)
        self.assertEqual(result["evaluation"]["status"], expected_status)

        self.liquidity_analyzer_mock.evaluate_liquidity.assert_called_once_with(
            event_id=event_id,
            metric=metric_name,
            value=metric_value,
            stream_size=len(stream_content)
        )

        self.db_storage_mock.store_macro_metric.assert_called_once_with(
            event_id=event_id,
            metric=metric_name,
            value=metric_value,
            evaluation={"score": expected_score, "status": expected_status}
        )

    def test_process_macro_event_missing_dependencies(self):
        bridge_no_deps = MacroLiquidityBridge(db_storage=None, liquidity_analyzer=None)

        event_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = random.uniform(1.0, 50.0)

        payload = {
            "metric": metric_name,
            "value": metric_value,
            "raw_stream": None
        }

        result = bridge_no_deps.process_macro_event(event_id=event_id, payload=payload)

        self.assertIn("trace_id", result)
        self.assertEqual(result["event_id"], event_id)
        self.assertIsNone(result["db_key"])
        self.assertEqual(result["evaluation"], {"score": 0.0, "status": "processed"})

    def test_process_macro_event_malformed_stream(self):
        event_id = uuid.uuid4().hex
        payload = {
            "metric": uuid.uuid4().hex,
            "value": random.randint(1, 100),
            "raw_stream": "not_a_bytes_io_object"
        }

        self.liquidity_analyzer_mock.evaluate_liquidity.return_value = {"score": 0.5, "status": "ok"}
        self.db_storage_mock.store_macro_metric.return_value = uuid.uuid4().hex

        result = self.bridge.process_macro_event(event_id=event_id, payload=payload)

        self.liquidity_analyzer_mock.evaluate_liquidity.assert_called_once_with(
            event_id=event_id,
            metric=payload["metric"],
            value=payload["value"],
            stream_size=0
        )
        self.assertEqual(result["event_id"], event_id)

if __name__ == '__main__':
    unittest.main()