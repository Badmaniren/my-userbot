import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)


class TestMarketPortfolioRealtimeStreamAnalyticsHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.stream_source = f"wss://market.stream/{uuid.uuid4().hex}"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.output_path = f"/var/log/market_{uuid.uuid4().hex}.json"

    def test_init_sets_attributes(self):
        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        self.assertEqual(hub.storage_file, self.storage_file)
        self.assertEqual(hub.stream_source, self.stream_source)
        self.assertIsNotNone(hub.analytics_engine)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.market_portfolio_realtime_stream_ingestor")
    def test_process_stream(self, mock_ingestor):
        expected_result = {"status": "streaming", "id": uuid.uuid4().hex}
        mock_ingestor.start_new.return_value = expected_result

        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        context = {"session_id": uuid.uuid4().hex}
        result = hub.process_stream(context)

        mock_ingestor.start_new.assert_called_once_with(context, self.stream_source)
        self.assertEqual(result, expected_result)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.market_portfolio_realtime_stream_ingestor")
    def test_audit_stream_data(self, mock_ingestor):
        expected_result = {"audited": True, "token": uuid.uuid4().hex}
        mock_ingestor.market_portfolio_realtime_stream_ingestor.return_value = expected_result

        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        payload = {"data": uuid.uuid4().hex}
        result = hub.audit_stream_data(payload, self.output_path)

        mock_ingestor.market_portfolio_realtime_stream_ingestor.assert_called_once_with(payload, self.output_path)
        self.assertEqual(result, expected_result)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics")
    def test_get_realtime_metrics(self, mock_analytics_cls):
        mock_instance = mock_analytics_cls.return_value
        expected_metrics = {"symbol": self.symbol, "metric": random.random()}
        mock_instance.calculate_metrics.return_value = expected_metrics

        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        result = hub.get_realtime_metrics(self.symbol)

        mock_instance.load_data.assert_called_once_with(self.storage_file)
        mock_instance.calculate_metrics.assert_called_once_with(self.symbol)
        self.assertEqual(result, expected_metrics)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics")
    def test_evaluate_stream_performance(self, mock_analytics_cls):
        mock_instance = mock_analytics_cls.return_value
        expected_eval = {"symbol": self.symbol, "performance": random.choice(["optimal", "suboptimal", "critical"])}
        mock_instance.evaluate_performance.return_value = expected_eval

        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        result = hub.evaluate_stream_performance(self.symbol)

        mock_instance.load_data.assert_called_once_with(self.storage_file)
        mock_instance.evaluate_performance.assert_called_once_with(self.symbol)
        self.assertEqual(result, expected_eval)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics")
    def test_process_realtime_stream_hub_success(self, mock_analytics_cls):
        mock_instance = mock_analytics_cls.return_value
        expected_metrics = {"symbol": self.symbol, "status": "active", "val": random.randint(1, 100)}
        mock_instance.calculate_metrics.return_value = expected_metrics

        res = process_realtime_stream_hub(self.output_path, self.storage_file, self.symbol)

        mock_instance.load_data.assert_called_once_with(self.storage_file)
        mock_instance.calculate_metrics.assert_called_once_with(self.symbol)
        self.assertEqual(res["output_path"], self.output_path)
        self.assertEqual(res["storage_file"], self.storage_file)
        self.assertEqual(res["metrics"], expected_metrics)

    @patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics")
    def test_process_realtime_stream_hub_exception_fallback(self, mock_analytics_cls):
        mock_instance = mock_analytics_cls.return_value
        mock_instance.load_data.side_effect = Exception("Database connection failure")

        res = process_realtime_stream_hub(self.output_path, self.storage_file, self.symbol)

        mock_instance.load_data.assert_called_once_with(self.storage_file)
        self.assertEqual(res["output_path"], self.output_path)
        self.assertEqual(res["storage_file"], self.storage_file)
        self.assertEqual(res["metrics"], {"symbol": self.symbol, "status": "initialized"})