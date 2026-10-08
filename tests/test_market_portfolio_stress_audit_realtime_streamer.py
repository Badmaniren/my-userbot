import unittest
from unittest.mock import MagicMock, patch
import io
import os
import json
import uuid
import random
import string
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer

class TestMarketPortfolioStressAuditRealtimeStreamer(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer(db_storage=self.db_storage_mock)

    def test_init_default_storage(self):
        streamer_default = MarketPortfolioStressAuditRealtimeStreamer()
        self.assertIsNotNone(streamer_default.db_storage)

    def test_init_source_path_positional(self):
        test_path = "test_source.jsonl"
        streamer = MarketPortfolioStressAuditRealtimeStreamer(test_path)
        self.assertEqual(streamer.source_path, test_path)

    def test_init_source_path_kwarg(self):
        test_path = "test_source.jsonl"
        streamer = MarketPortfolioStressAuditRealtimeStreamer(source_path=test_path)
        self.assertEqual(streamer.source_path, test_path)

    def test_stream_events_from_source_path(self):
        test_path = f"tmp_test_stream_{uuid.uuid4().hex[:8]}.jsonl"
        records = [
            {"portfolio_id": "PF-1", "var_99": 100.5, "drawdown_pct": 5.2},
            {"portfolio_id": "PF-2", "var_99": 200.0, "drawdown_pct": 12.1}
        ]
        with open(test_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        try:
            streamer = MarketPortfolioStressAuditRealtimeStreamer(source_path=test_path)
            events = list(streamer.stream_events())
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["portfolio_id"], "PF-1")
            self.assertEqual(events[1]["portfolio_id"], "PF-2")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_stream_events_from_stdin_json(self):
        json_line = json.dumps({"portfolio_id": "PF-3", "var_99": 150.0}) + "\n"
        streamer = MarketPortfolioStressAuditRealtimeStreamer()

        with patch('sys.stdin', io.StringIO(json_line)):
            events = list(streamer.stream_events())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["portfolio_id"], "PF-3")

    def test_stream_and_persist_valid_float_metric(self):
        portfolio_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = round(random.uniform(1.0, 1000.0), 2)
        line = f"{portfolio_id}:{metric_name}:{metric_value}\n"

        with patch('sys.stdin', io.StringIO(line)):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertTrue(result)
        self.db_storage_mock.save_metric.assert_called_once_with(portfolio_id, metric_name, float(metric_value))

    def test_stream_and_persist_valid_string_metric(self):
        portfolio_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = ''.join(random.choices(string.ascii_uppercase, k=5))
        line = f"{portfolio_id}:{metric_name}:{metric_value}\n"

        with patch('sys.stdin', io.StringIO(line)):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertTrue(result)
        self.db_storage_mock.save_metric.assert_called_once_with(portfolio_id, metric_name, metric_value)

    def test_stream_and_persist_alternative_storage_method(self):
        portfolio_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = round(random.uniform(1.0, 100.0), 2)
        line = f"{portfolio_id}:{metric_name}:{metric_value}\n"

        del self.db_storage_mock.save_metric
        self.db_storage_mock.save_portfolio_metric = MagicMock()

        with patch('sys.stdin', io.StringIO(line)):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertTrue(result)
        self.db_storage_mock.save_portfolio_metric.assert_called_once_with(portfolio_id, metric_name, float(metric_value))

    def test_stream_and_persist_bytes_input(self):
        portfolio_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = round(random.uniform(1.0, 100.0), 2)
        line_bytes = f"{portfolio_id}:{metric_name}:{metric_value}\n".encode('utf-8')

        mock_stdin = MagicMock()
        mock_stdin.readline.return_value = line_bytes

        with patch('sys.stdin', mock_stdin):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertTrue(result)
        self.db_storage_mock.save_metric.assert_called_once()

    def test_stream_and_persist_empty_line(self):
        portfolio_id = uuid.uuid4().hex
        with patch('sys.stdin', io.StringIO("\n")):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertFalse(result)
        self.db_storage_mock.save_metric.assert_not_called()

    def test_stream_and_persist_mismatched_portfolio_id(self):
        portfolio_id = uuid.uuid4().hex
        other_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = round(random.uniform(1.0, 100.0), 2)
        line = f"{other_id}:{metric_name}:{metric_value}\n"

        with patch('sys.stdin', io.StringIO(line)):
            result = self.streamer.stream_and_persist(portfolio_id)

        self.assertFalse(result)
        self.db_storage_mock.save_metric.assert_not_called()

    def test_process_stream_chunk_anomaly_detected(self):
        detector_mock = MagicMock()
        detector_mock.evaluate.return_value = True
        self.streamer.market_anomaly_detector = detector_mock

        chunk_data = {uuid.uuid4().hex: random.randint(1, 100)}
        result = self.streamer.process_stream_chunk(chunk_data)

        self.assertTrue(result)
        detector_mock.evaluate.assert_called_once_with(chunk_data)

    def test_process_stream_chunk_no_anomaly(self):
        detector_mock = MagicMock()
        detector_mock.evaluate.return_value = False
        self.streamer.market_anomaly_detector = detector_mock

        chunk_data = {uuid.uuid4().hex: random.randint(1, 100)}
        result = self.streamer.process_stream_chunk(chunk_data)

        self.assertFalse(result)
        detector_mock.evaluate.assert_called_once_with(chunk_data)

    def test_process_stream_chunk_no_detector(self):
        self.streamer.market_anomaly_detector = None
        chunk_data = {uuid.uuid4().hex: random.randint(1, 100)}
        result = self.streamer.process_stream_chunk(chunk_data)

        self.assertFalse(result)

    def test_get_live_audit_metrics_success(self):
        unique_key = uuid.uuid4().hex
        expected_metrics = {uuid.uuid4().hex: random.randint(1, 500)}
        self.db_storage_mock.fetch_latest_audit.return_value = expected_metrics

        metrics = self.streamer.get_live_audit_metrics(unique_key)

        self.assertEqual(metrics, expected_metrics)
        self.db_storage_mock.fetch_latest_audit.assert_called_once_with(unique_key)

    def test_get_live_audit_metrics_missing_method(self):
        unique_key = uuid.uuid4().hex
        del self.db_storage_mock.fetch_latest_audit

        metrics = self.streamer.get_live_audit_metrics(unique_key)

        self.assertEqual(metrics, {})

    def test_emit_stress_event_success(self):
        sink_mock = MagicMock()
        self.streamer.market_portfolio_alert_event_sink = sink_mock

        event_tag = uuid.uuid4().hex
        event_value = random.randint(10, 1000)

        self.streamer.emit_stress_event(event_tag, event_value)

        sink_mock.push.assert_called_once_with({
            "tag": event_tag,
            "value": event_value
        })

    def test_emit_stress_event_no_sink(self):
        self.streamer.market_portfolio_alert_event_sink = None
        event_tag = uuid.uuid4().hex
        event_value = random.randint(10, 1000)

        try:
            self.streamer.emit_stress_event(event_tag, event_value)
        except Exception as e:
            self.fail(f"emit_stress_event raised exception when sink is None: {e}")

    def test_stream_audit_metrics(self):
        portfolio_id = uuid.uuid4().hex
        result = self.streamer.stream_audit_metrics(portfolio_id)

        self.assertIn("stream_id", result)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(uuid.UUID(result["stream_id"]))

if __name__ == '__main__':
    unittest.main()
