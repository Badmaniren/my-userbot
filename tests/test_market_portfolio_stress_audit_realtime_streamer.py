import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer

class TestMarketPortfolioStressAuditRealtimeStreamer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer(db_storage=self.db_storage)

    def test_stream_metrics_persistence_and_broadcast(self):
        portfolio_id = str(uuid.uuid4())
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(100.0, 9999.9)

        raw_payload = f"{portfolio_id}:{metric_name}:{metric_value}"
        stream_source = io.BytesIO(raw_payload.encode('utf-8'))

        with patch('skills.market_portfolio_stress_audit_realtime_streamer.sys.stdin', stream_source):
            result = self.streamer.stream_and_persist(portfolio_id=portfolio_id)

        self.assertTrue(result)
        self.db_storage.save_metric.assert_called_once()
        saved_args = self.db_storage.save_metric.call_args[0]
        self.assertIn(portfolio_id, str(saved_args))
        self.assertIn(metric_name, str(saved_args))

    def test_realtime_anomaly_trigger_on_chaos_stream(self):
        stream_id = uuid.uuid4().hex
        random_threshold = random.randint(50, 500)
        
        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.evaluate.return_value = True

        self.streamer.market_anomaly_detector = mock_anomaly_detector

        with patch('skills.market_portfolio_stress_audit_realtime_streamer.uuid.uuid4', return_value=uuid.UUID(stream_id)):
            alert_dispatched = self.streamer.process_stream_chunk(
                chunk_data={"stream_id": stream_id, "spike": random_threshold * 10}
            )

        self.assertTrue(alert_dispatched)
        mock_anomaly_detector.evaluate.assert_called_once()

    def test_db_storage_integration_without_mock_overrides(self):
        unique_key = uuid.uuid4().hex
        random_score = random.random()

        self.db_storage.fetch_latest_audit.return_value = {
            "key": unique_key,
            "score": random_score
        }

        audit_data = self.streamer.get_live_audit_metrics(unique_key)

        self.assertEqual(audit_data["key"], unique_key)
        self.assertEqual(audit_data["score"], random_score)
        self.db_storage.fetch_latest_audit.assert_called_once_with(unique_key)

    def test_pipeline_event_sink_dispatch(self):
        event_tag = ''.join(random.choices(string.ascii_uppercase, k=8))
        payload_value = random.randint(1000, 99999)

        mock_sink = MagicMock()
        self.streamer.market_portfolio_alert_event_sink = mock_sink

        self.streamer.emit_stress_event(event_tag=event_tag, value=payload_value)

        mock_sink.push.assert_called_once()
        dispatched_data = mock_sink.push.call_args[0][0]
        self.assertEqual(dispatched_data["tag"], event_tag)
        self.assertEqual(dispected_value := dispatched_data["value"], payload_value)

if __name__ == '__main__':
    unittest.main()