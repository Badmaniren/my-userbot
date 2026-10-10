import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_realtime_stream_dashboard_bridge import (
    market_portfolio_realtime_stream_dashboard_bridge,
    process_dashboard_stream_bridge
)


class TestMarketPortfolioRealtimeStreamDashboardBridge(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"/tmp/{uuid.uuid4().hex}.db"
        self.random_stream_source = f"stream://{uuid.uuid4().hex}"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_output_path = f"/var/log/{uuid.uuid4().hex}.json"
        self.random_url = f"https://{uuid.uuid4().hex}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_threshold = round(random.uniform(1.0, 100.0), 2)
        self.random_channels = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.random_payload = {
            "event_id": uuid.uuid4().hex,
            "metric": random.choice(["volume", "price", "volatility"]),
            "value": random.randint(10, 5000)
        }

    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub')
    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.market_portfolio_realtime_stream_alert_sink')
    def test_bridge_execution_success(self, mock_alert_sink, mock_analytics_hub_cls):
        mock_hub_instance = MagicMock()
        expected_analytics_result = {
            "status": "processed",
            "symbol": self.random_symbol,
            "metric_value": self.random_payload["value"]
        }
        mock_hub_instance.process_stream.return_value = expected_analytics_result
        mock_analytics_hub_cls.return_value = mock_hub_instance

        expected_sink_result = {
            "dispatched": True,
            "channels_count": len(self.random_channels)
        }
        mock_alert_sink.return_value = expected_sink_result

        context = {
            "stream_source": self.random_stream_source,
            "payload": self.random_payload
        }

        result = market_portfolio_realtime_stream_dashboard_bridge(
            storage_file=self.random_storage,
            stream_source=self.random_stream_source,
            output_path=self.random_output_path,
            symbol=self.random_symbol,
            url=self.random_url,
            token=self.random_token,
            chat_id=self.random_chat_id,
            severity=self.random_severity,
            threshold=self.random_threshold,
            channels=self.random_channels,
            payload=self.random_payload,
            context=context
        )

        self.assertIn("analytics", result)
        self.assertIn("alert_sink", result)
        self.assertEqual(result["analytics"], expected_analytics_result)
        self.assertEqual(result["alert_sink"], expected_sink_result)

        mock_analytics_hub_cls.assert_called_once_with(
            storage_file=self.random_storage,
            stream_source=self.random_stream_source
        )
        mock_hub_instance.process_stream.assert_called_once_with(context)
        mock_alert_sink.assert_called_once_with(
            payload=self.random_payload,
            output_path=self.random_output_path,
            storage=self.random_storage,
            url=self.random_url,
            token=self.random_token,
            chat_id=self.random_chat_id,
            severity=self.random_severity,
            threshold=self.random_threshold,
            channels=self.random_channels,
            symbol=self.random_symbol
        )

    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub')
    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.market_portfolio_realtime_stream_alert_sink')
    def test_process_dashboard_stream_bridge_wrapper(self, mock_alert_sink, mock_analytics_hub_cls):
        mock_hub_instance = MagicMock()
        mock_hub_instance.get_realtime_metrics.return_value = {
            "symbol": self.random_symbol,
            "score": random.randint(1, 100)
        }
        mock_analytics_hub_cls.return_value = mock_hub_instance

        mock_alert_sink.return_value = {"status": "ok"}

        result = process_dashboard_stream_bridge(
            output_path=self.random_output_path,
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            url=self.random_url,
            token=self.random_token,
            chat_id=self.random_chat_id,
            severity=self.random_severity,
            threshold=self.random_threshold,
            channels=self.random_channels
        )

        self.assertIsInstance(result, dict)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["symbol"], self.random_symbol)
        mock_hub_instance.get_realtime_metrics.assert_called_once_with(self.random_symbol)

    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub')
    def test_analytics_hub_exception_handling(self, mock_analytics_hub_cls):
        mock_hub_instance = MagicMock()
        random_error_msg = f"Stream failure {uuid.uuid4().hex}"
        mock_hub_instance.process_stream.side_effect = Exception(random_error_msg)
        mock_analytics_hub_cls.return_value = mock_hub_instance

        context = {"stream_source": self.random_stream_source}

        with self.assertRaises(Exception) as ctx:
            market_portfolio_realtime_stream_dashboard_bridge(
                storage_file=self.random_storage,
                stream_source=self.random_stream_source,
                output_path=self.random_output_path,
                symbol=self.random_symbol,
                url=self.random_url,
                token=self.random_token,
                chat_id=self.random_chat_id,
                severity=self.random_severity,
                threshold=self.random_threshold,
                channels=self.random_channels,
                payload=self.random_payload,
                context=context
            )

        self.assertIn(random_error_msg, str(ctx.exception))

    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub')
    @patch('skills.market_portfolio_realtime_stream_dashboard_bridge.market_portfolio_realtime_stream_alert_sink')
    def test_io_stream_payload_handling(self, mock_alert_sink, mock_analytics_hub_cls):
        mock_hub_instance = MagicMock()
        mock_hub_instance.audit_stream_data.return_value = {"audited": True}
        mock_analytics_hub_cls.return_value = mock_hub_instance

        mock_alert_sink.return_value = {"dispatched": True}

        random_binary_garbage = f"binary_data_{uuid.uuid4().hex}".encode('utf-8')
        io_stream_mock = io.BytesIO(random_binary_garbage)

        context = {
            "stream_source": io_stream_mock,
            "payload": self.random_payload
        }

        result = market_portfolio_realtime_stream_dashboard_bridge(
            storage_file=self.random_storage,
            stream_source=self.random_stream_source,
            output_path=self.random_output_path,
            symbol=self.random_symbol,
            url=self.random_url,
            token=self.random_token,
            chat_id=self.random_chat_id,
            severity=self.random_severity,
            threshold=self.random_threshold,
            channels=self.random_channels,
            payload=self.random_payload,
            context=context
        )

        self.assertIsNotNone(result)
        mock_hub_instance.process_stream.assert_called_once_with(context)


if __name__ == '__main__':
    unittest.main()