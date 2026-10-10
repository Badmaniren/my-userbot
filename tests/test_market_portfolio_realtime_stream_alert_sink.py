import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_realtime_stream_alert_sink import (
    process_stream_and_dispatch_alerts,
    stream_alert_sink_handler,
    market_portfolio_realtime_stream_alert_sink
)

class TestMarketPortfolioRealtimeStreamAlertSink(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.rand_url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1/stream"
        self.rand_token = uuid.uuid4().hex
        self.rand_chat_id = str(random.randint(100000, 99999999))
        self.rand_output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.rand_threshold = round(random.uniform(1.0, 100.0), 2)
        self.rand_channels = [random.choice(["telegram", "webhook", "email"])]
        self.rand_stream_source = f"stream://{uuid.uuid4().hex[:8]}"
        self.rand_context = {"session_id": uuid.uuid4().hex}
        self.rand_payload = {
            "symbol": self.rand_symbol,
            "price": round(random.uniform(10.0, 1000.0), 2),
            "volume": random.randint(100, 5000)
        }

    @patch('skills.market_portfolio_realtime_stream_ingestor.start_new')
    @patch('skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_alert_event_sink.handle_portfolio_alert_event')
    def test_process_stream_and_dispatch_alerts_logic(
        self, mock_handle_alert, mock_ingestor_func, mock_start_new
    ):
        expected_ingest_result = {"status": "success", "data": uuid.uuid4().hex}
        expected_alert_result = {"dispatched": True, "alert_id": uuid.uuid4().hex}

        mock_start_new.return_value = expected_ingest_result
        mock_ingestor_func.return_value = {"processed": True}
        mock_handle_alert.return_value = expected_alert_result

        result = process_stream_and_dispatch_alerts(
            context=self.rand_context,
            stream_source=self.rand_stream_source,
            payload=self.rand_payload,
            output_path=self.rand_output_path,
            symbol=self.rand_symbol,
            url=self.rand_url,
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage=MagicMock(),
            severity=self.rand_severity,
            threshold=self.rand_threshold,
            channels=self.rand_channels
        )

        mock_start_new.assert_called_once_with(self.rand_context, self.rand_stream_source)
        mock_ingestor_func.assert_called_once_with(self.rand_payload, self.rand_output_path)
        mock_handle_alert.assert_called_once_with(
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            unittest.mock.ANY,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        self.assertEqual(result["ingest_result"], expected_ingest_result)
        self.assertEqual(result["alert_dispatched"], expected_alert_result)

    @patch('skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_alert_event_sink.route_and_sink_alerts')
    def test_stream_alert_sink_handler_logic(
        self, mock_route_and_sink, mock_ingestor_func
    ):
        expected_routing_result = {"routed": True, "sink_id": uuid.uuid4().hex}
        mock_route_and_sink.return_value = expected_routing_result
        mock_ingestor_func.return_value = {"status": "ok"}

        mock_storage = MagicMock()

        result = stream_alert_sink_handler(
            storage=mock_storage,
            symbol=self.rand_symbol,
            url=self.rand_url,
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            severity=self.rand_severity,
            threshold=self.rand_threshold,
            channels=self.rand_channels,
            payload=self.rand_payload,
            output_path=self.rand_output_path
        )

        mock_ingestor_func.assert_called_once_with(self.rand_payload, self.rand_output_path)
        mock_route_and_sink.assert_called_once_with(
            mock_storage,
            self.rand_symbol,
            self.rand_url,
            self.rand_token,
            self.rand_chat_id,
            self.rand_severity,
            self.rand_threshold,
            self.rand_channels
        )

        self.assertEqual(result["routing_result"], expected_routing_result)

    @patch('skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_alert_event_sink.handle_portfolio_alert_event')
    @patch('skills.market_portfolio_alert_event_sink.route_and_sink_alerts')
    def test_market_portfolio_realtime_stream_alert_sink_default_symbol(
        self, mock_route, mock_handle, mock_ingestor
    ):
        payload_without_symbol = {
            "price": round(random.uniform(50.0, 500.0), 2)
        }
        
        mock_handle.return_value = {"handled": True}
        mock_route.return_value = {"routed": True}
        mock_ingestor.return_value = {"ingested": True}

        result = market_portfolio_realtime_stream_alert_sink(
            payload=payload_without_symbol,
            output_path=self.rand_output_path,
            storage=MagicMock(),
            url=self.rand_url,
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            severity=self.rand_severity,
            threshold=self.rand_threshold,
            channels=self.rand_channels,
            symbol=None
        )

        mock_handle.assert_called_once_with(
            symbol="DEFAULT_SYM",
            url=self.rand_url,
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage=unittest.mock.ANY,
            severity=self.rand_severity,
            threshold=self.rand_threshold,
            channels=self.rand_channels
        )
        self.assertIn("sink_result", result)
        self.assertIn("route_result", result)

    @patch('skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_alert_event_sink.handle_portfolio_alert_event')
    @patch('skills.market_portfolio_alert_event_sink.route_and_sink_alerts')
    def test_market_portfolio_realtime_stream_alert_sink_payload_symbol(
        self, mock_route, mock_handle, mock_ingestor
    ):
        custom_payload_symbol = f"PAYLOAD_SYM_{uuid.uuid4().hex[:4]}"
        payload_with_symbol = {
            "symbol": custom_payload_symbol,
            "value": random.randint(1, 100)
        }

        mock_handle.return_value = {"status": uuid.uuid4().hex}
        mock_route.return_value = {"status": uuid.uuid4().hex}

        market_portfolio_realtime_stream_alert_sink(
            payload=payload_with_symbol,
            output_path=self.rand_output_path,
            storage=MagicMock(),
            url=self.rand_url,
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            severity=self.rand_severity,
            threshold=self.rand_threshold,
            channels=self.rand_channels,
            symbol=None
        )

        mock_handle.assert_called_once()
        called_kwargs = mock_handle.call_args[1]
        self.assertEqual(called_kwargs["symbol"], custom_payload_symbol)

    def test_stream_io_bytes_mocking(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8'))
        self.assertIsInstance(stream_data.read(), bytes)

if __name__ == '__main__':
    unittest.main()