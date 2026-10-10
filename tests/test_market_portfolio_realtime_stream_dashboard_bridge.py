import unittest
from unittest.mock import patch
import uuid
import random
import io
from skills.market_portfolio_realtime_stream_dashboard_bridge import (
    MarketPortfolioRealtimeStreamDashboardBridge,
    market_portfolio_realtime_stream_dashboard_bridge,
    process_dashboard_stream_bridge,
    process_dashboard_bridge_stream
)


class TestMarketPortfolioRealtimeStreamDashboardBridge(unittest.TestCase):

    def test_dashboard_bridge_class_process_and_bridge(self):
        rand_storage = uuid.uuid4().hex
        rand_source = uuid.uuid4().hex
        rand_path = uuid.uuid4().hex + ".json"
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 9999)
        
        bridge = MarketPortfolioRealtimeStreamDashboardBridge(
            storage_file=rand_storage,
            stream_source=rand_source
        )

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_instance = MockHub.return_value
            mock_instance.process_stream.return_value = {rand_key: rand_val}
            
            context = {"metrics": {rand_key: rand_val}}
            result = bridge.process_and_bridge(context=context, output_path=rand_path)

            self.assertEqual(result, {rand_key: rand_val})
            mock_instance.process_stream.assert_called_once_with(context)
            mock_instance.audit_stream_data.assert_called_once_with(context["metrics"], rand_path)

    def test_dashboard_bridge_class_process_stream_empty_context(self):
        bridge = MarketPortfolioRealtimeStreamDashboardBridge()

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_instance = MockHub.return_value
            rand_key = uuid.uuid4().hex
            rand_val = uuid.uuid4().hex
            mock_instance.process_stream.return_value = {rand_key: rand_val}

            result = bridge.process_stream()

            self.assertEqual(result, {rand_key: rand_val})
            mock_instance.process_stream.assert_called_once_with(None)

    def test_dashboard_bridge_class_get_realtime_metrics(self):
        rand_symbol = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.random()

        bridge = MarketPortfolioRealtimeStreamDashboardBridge()

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_instance = MockHub.return_value
            mock_instance.get_realtime_metrics.return_value = {rand_metric_key: rand_metric_val}

            metrics = bridge.get_realtime_metrics(rand_symbol)

            self.assertEqual(metrics, {rand_metric_key: rand_metric_val})
            mock_instance.get_realtime_metrics.assert_called_once_with(rand_symbol)

    def test_market_portfolio_realtime_stream_dashboard_bridge_function(self):
        rand_storage = uuid.uuid4().hex
        rand_source = uuid.uuid4().hex
        rand_output = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex
        rand_url = f"https://{uuid.uuid4().hex}.com"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_severity = uuid.uuid4().hex
        rand_threshold = random.uniform(0.1, 99.9)
        rand_channels = [uuid.uuid4().hex]
        rand_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_context = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub, \
             patch("skills.market_portfolio_realtime_stream_dashboard_bridge.market_portfolio_realtime_stream_alert_sink") as mock_sink:
            
            mock_hub_instance = MockHub.return_value
            rand_analytics_res = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_hub_instance.process_stream.return_value = rand_analytics_res

            rand_sink_res = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_sink.return_value = rand_sink_res

            res = market_portfolio_realtime_stream_dashboard_bridge(
                storage_file=rand_storage,
                stream_source=rand_source,
                output_path=rand_output,
                symbol=rand_symbol,
                url=rand_url,
                token=rand_token,
                chat_id=rand_chat,
                severity=rand_severity,
                threshold=rand_threshold,
                channels=rand_channels,
                payload=rand_payload,
                context=rand_context
            )

            self.assertEqual(res["analytics"], rand_analytics_res)
            self.assertEqual(res["alert_sink"], rand_sink_res)
            MockHub.assert_called_once_with(storage_file=rand_storage, stream_source=rand_source)
            mock_hub_instance.process_stream.assert_called_once_with(rand_context)
            mock_sink.assert_called_once_with(
                payload=rand_payload,
                output_path=rand_output,
                storage=rand_storage,
                url=rand_url,
                token=rand_token,
                chat_id=rand_chat,
                severity=rand_severity,
                threshold=rand_threshold,
                channels=rand_channels,
                symbol=rand_symbol
            )

    def test_process_dashboard_stream_bridge(self):
        rand_storage = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex
        rand_output = uuid.uuid4().hex
        rand_url = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_chat = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        rand_threshold = random.random()
        rand_channels = [uuid.uuid4().hex]

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_hub_instance = MockHub.return_value
            rand_metrics = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_hub_instance.get_realtime_metrics.return_value = rand_metrics

            res = process_dashboard_stream_bridge(
                output_path=rand_output,
                storage_file=rand_storage,
                symbol=rand_symbol,
                url=rand_url,
                token=rand_token,
                chat_id=rand_chat,
                severity=rand_severity,
                threshold=rand_threshold,
                channels=rand_channels
            )

            self.assertEqual(res, {"metrics": rand_metrics})
            MockHub.assert_called_once_with(storage_file=rand_storage, stream_source=None)
            mock_hub_instance.get_realtime_metrics.assert_called_once_with(rand_symbol)

    def test_process_dashboard_bridge_stream_with_payload(self):
        rand_storage = uuid.uuid4().hex
        rand_source = uuid.uuid4().hex
        rand_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_output = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_hub_instance = MockHub.return_value
            rand_metrics = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_hub_instance.get_realtime_metrics.return_value = rand_metrics

            res = process_dashboard_bridge_stream(
                storage=rand_storage,
                stream_source=rand_source,
                payload=rand_payload,
                output_path=rand_output,
                symbol=rand_symbol
            )

            self.assertEqual(res, rand_metrics)
            MockHub.assert_called_once_with(storage_file=rand_storage, stream_source=rand_source)
            mock_hub_instance.audit_stream_data.assert_called_once_with(rand_payload, rand_output)
            mock_hub_instance.get_realtime_metrics.assert_called_once_with(rand_symbol)

    def test_process_dashboard_bridge_stream_fallback(self):
        rand_storage = uuid.uuid4().hex
        rand_symbol = uuid.uuid4().hex

        with patch("skills.market_portfolio_realtime_stream_dashboard_bridge.MarketPortfolioRealtimeStreamAnalyticsHub") as MockHub:
            mock_hub_instance = MockHub.return_value
            mock_hub_instance.get_realtime_metrics.return_value = None

            res = process_dashboard_bridge_stream(
                storage=rand_storage,
                symbol=rand_symbol
            )

            self.assertEqual(res, {"status": "ok"})
            mock_hub_instance.get_realtime_metrics.assert_called_once_with(rand_symbol)


if __name__ == "__main__":
    unittest.main()