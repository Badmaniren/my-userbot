import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer

class TestMarketPortfolioStressAuditRealtimeStreamer(unittest.TestCase):
    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer(db_storage=self.db_storage_mock)
        self.portfolio_id = uuid.uuid4().hex
        self.metric_name = uuid.uuid4().hex
        self.metric_value = round(random.uniform(10.0, 1000.0), 2)

    def test_stream_and_persist_success(self):
        line_content = f"{self.portfolio_id}:{self.metric_name}:{self.metric_value}\n"
        stream_mock = io.BytesIO(line_content.encode('utf-8'))
        
        with patch('sys.stdin', stream_mock):
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertTrue(result)
            self.db_storage_mock.save_metric.assert_called_once_with(
                self.portfolio_id, self.metric_name, self.metric_value
            )

    def test_stream_and_persist_alternative_method(self):
        del self.db_storage_mock.save_metric
        line_content = f"{self.portfolio_id}:{self.metric_name}:{self.metric_value}\n"
        stream_mock = io.BytesIO(line_content.encode('utf-8'))
        
        with patch('sys.stdin', stream_mock):
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertTrue(result)
            self.db_storage_mock.save_portfolio_metric.assert_called_once_with(
                self.portfolio_id, self.metric_name, self.metric_value
            )

    def test_stream_and_persist_empty_line(self):
        stream_mock = io.BytesIO(b"")
        with patch('sys.stdin', stream_mock):
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertFalse(result)

    def test_stream_and_persist_wrong_portfolio(self):
        other_portfolio_id = uuid.uuid4().hex
        line_content = f"{other_portfolio_id}:{self.metric_name}:{self.metric_value}\n"
        stream_mock = io.BytesIO(line_content.encode('utf-8'))
        
        with patch('sys.stdin', stream_mock):
            result = self.streamer.stream_and_persist(self.portfolio_id)
            self.assertFalse(result)
            self.db_storage_mock.save_metric.assert_not_called()

    def test_process_stream_chunk_anomaly(self):
        detector_mock = MagicMock()
        detector_mock.evaluate.return_value = True
        self.streamer.market_anomaly_detector = detector_mock
        
        chunk = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = self.streamer.process_stream_chunk(chunk)
        self.assertTrue(result)
        detector_mock.evaluate.assert_called_once_with(chunk)

    def test_process_stream_chunk_no_anomaly(self):
        detector_mock = MagicMock()
        detector_mock.evaluate.return_value = False
        self.streamer.market_anomaly_detector = detector_mock
        
        chunk = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = self.streamer.process_stream_chunk(chunk)
        self.assertFalse(result)
        detector_mock.evaluate.assert_called_once_with(chunk)

    def test_process_stream_chunk_no_detector(self):
        self.streamer.market_anomaly_detector = None
        chunk = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = self.streamer.process_stream_chunk(chunk)
        self.assertFalse(result)

    def test_get_live_audit_metrics(self):
        unique_key = uuid.uuid4().hex
        expected_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.db_storage_mock.fetch_latest_audit.return_value = expected_data
        
        result = self.streamer.get_live_audit_metrics(unique_key)
        self.assertEqual(result, expected_data)
        self.db_storage_mock.fetch_latest_audit.assert_called_once_with(unique_key)

    def test_get_live_audit_metrics_missing_method(self):
        del self.db_storage_mock.fetch_latest_audit
        unique_key = uuid.uuid4().hex
        result = self.streamer.get_live_audit_metrics(unique_key)
        self.assertEqual(result, {})

    def test_emit_stress_event(self):
        sink_mock = MagicMock()
        self.streamer.market_portfolio_alert_event_sink = sink_mock
        event_tag = uuid.uuid4().hex
        event_value = random.randint(-1000, 1000)
        
        self.streamer.emit_stress_event(event_tag, event_value)
        sink_mock.push.assert_called_once_with({
            "tag": event_tag,
            "value": event_value
        })

    def test_emit_stress_event_no_sink(self):
        self.streamer.market_portfolio_alert_event_sink = None
        event_tag = uuid.uuid4().hex
        event_value = random.randint(-1000, 1000)
        try:
            self.streamer.emit_stress_event(event_tag, event_value)
        except Exception as e:
            self.fail(f"emit_stress_event raised exception without sink: {e}")

    def test_stream_audit_metrics(self):
        result = self.streamer.stream_audit_metrics(self.portfolio_id)
        self.assertIn("stream_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertTrue(uuid.UUID(result["stream_id"]))

if __name__ == '__main__':
    unittest.main()