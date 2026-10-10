import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_portfolio_realtime_stream_alert_sink import (
    process_stream_and_dispatch_alerts,
    stream_alert_sink_handler
)

class TestMarketPortfolioRealtimeStreamAlertSink(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.rand_url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1/stream"
        self.rand_token = uuid.uuid4().hex
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_storage = f"/tmp/{uuid.uuid4().hex}.db"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.rand_threshold = round(random.uniform(1.0, 99.9), 2)
        self.rand_channels = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        self.rand_output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.rand_stream_source = f"wss://stream.{uuid.uuid4().hex[:8]}.org/ws"
        self.rand_payload_key = uuid.uuid4().hex
        self.rand_payload_val = uuid.uuid4().hex

    def test_process_stream_and_dispatch_alerts_success(self):
        payload = {self.rand_payload_key: self.rand_payload_val}
        ingest_result = {uuid.uuid4().hex: uuid.uuid4().hex, "status": "processed"}
        
        with patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_alert_event_sink') as mock_sink:
            
            mock_ingestor.start_new.return_value = ingest_result
            mock_sink.handle_portfolio_alert_event.return_value = True

            context = {uuid.uuid4().hex: uuid.uuid4().hex}
            
            result = process_stream_and_dispatch_alerts(
                context=context,
                stream_source=self.rand_stream_source,
                payload=payload,
                output_path=self.rand_output_path,
                symbol=self.rand_symbol,
                url=self.rand_url,
                token=self.rand_token,
                chat_id=self.rand_chat_id,
                storage=self.rand_storage,
                severity=self.rand_severity,
                threshold=self.rand_threshold,
                channels=self.rand_channels
            )

            mock_ingestor.start_new.assert_called_once_with(context, self.rand_stream_source)
            mock_ingestor.market_portfolio_realtime_stream_ingestor.assert_called_once_with(payload, self.rand_output_path)
            mock_sink.handle_portfolio_alert_event.assert_called_once_with(
                self.rand_symbol,
                self.rand_url,
                self.rand_token,
                self.rand_chat_id,
                self.rand_storage,
                self.rand_severity,
                self.rand_threshold,
                self.rand_channels
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("ingest_result"), ingest_result)
            self.assertTrue(result.get("alert_dispatched"))

    def test_stream_alert_sink_handler_execution(self):
        mock_data_chunk = uuid.uuid4().hex.encode('utf-8')
        mock_file_stream = io.BytesIO(mock_data_chunk)

        with patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_alert_event_sink') as mock_sink:

            mock_ingestor.market_portfolio_realtime_stream_ingestor.return_value = {uuid.uuid4().hex: mock_file_stream}
            mock_sink.route_and_sink_alerts.return_value = {uuid.uuid4().hex: random.randint(1, 100)}

            res = stream_alert_sink_handler(
                storage=self.rand_storage,
                symbol=self.rand_symbol,
                url=self.rand_url,
                token=self.rand_token,
                chat_id=self.rand_chat_id,
                severity=self.rand_severity,
                threshold=self.rand_threshold,
                channels=self.rand_channels,
                payload={uuid.uuid4().hex: uuid.uuid4().hex},
                output_path=self.rand_output_path
            )

            mock_sink.route_and_sink_alerts.assert_called_once_with(
                self.rand_storage,
                self.rand_symbol,
                self.rand_url,
                self.rand_token,
                self.rand_chat_id,
                self.rand_severity,
                self.rand_threshold,
                self.rand_channels
            )
            self.assertIn("routing_result", res)

    def test_process_stream_and_dispatch_alerts_failure_handling(self):
        with patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_realtime_stream_ingestor') as mock_ingestor, \
             patch('skills.market_portfolio_realtime_stream_alert_sink.market_portfolio_alert_event_sink') as mock_sink:

            mock_ingestor.start_new.side_effect = Exception(uuid.uuid4().hex)

            context = {}
            payload = {}

            with self.assertRaises(Exception):
                process_stream_and_dispatch_alerts(
                    context=context,
                    stream_source=self.rand_stream_source,
                    payload=payload,
                    output_path=self.rand_output_path,
                    symbol=self.rand_symbol,
                    url=self.rand_url,
                    token=self.rand_token,
                    chat_id=self.rand_chat_id,
                    storage=self.rand_storage,
                    severity=self.rand_severity,
                    threshold=self.rand_threshold,
                    channels=self.rand_channels
                )

            mock_sink.handle_portfolio_alert_event.assert_not_called()

if __name__ == '__main__':
    unittest.main()