import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)


class TestMarketPortfolioRealtimeStreamAnalyticsHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.stream_source = f"wss://stream.{uuid.uuid4().hex}.net/feed"
        self.hub = MarketPortfolioRealtimeStreamAnalyticsHub(
            storage_file=self.storage_file,
            stream_source=self.stream_source
        )

    def test_init_attributes(self):
        self.assertEqual(self.hub.storage_file, self.storage_file)
        self.assertEqual(self.hub.stream_source, self.stream_source)
        self.assertIsNotNone(self.hub.analytics_engine)

    def test_process_stream_success(self):
        context_key = uuid.uuid4().hex
        context_value = uuid.uuid4().hex
        context = {context_key: context_value}
        
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_realtime_stream_analytics_hub.market_portfolio_realtime_stream_ingestor.start_new", return_value=expected_result) as mock_start:
            res = self.hub.process_stream(context)
            mock_start.assert_called_once_with(context, self.stream_source)
            self.assertEqual(res, expected_result)

    def test_process_stream_exception(self):
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        error_message = f"error_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_realtime_stream_analytics_hub.market_portfolio_realtime_stream_ingestor.start_new", side_effect=Exception(error_message)) as mock_start:
            res = self.hub.process_stream(context)
            mock_start.assert_called_once_with(context, self.stream_source)
            self.assertEqual(res["status"], "error")
            self.assertEqual(res["message"], error_message)
            self.assertEqual(res["context"], context)

    def test_audit_stream_data(self):
        payload = {uuid.uuid4().hex: random.randint(1, 1000)}
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_audit_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_realtime_stream_analytics_hub.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor", return_value=expected_audit_result) as mock_audit:
            res = self.hub.audit_stream_data(payload, output_path)
            mock_audit.assert_called_once_with(payload, output_path)
            self.assertEqual(res, expected_audit_result)

    def test_get_realtime_metrics(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        expected_metrics = {uuid.uuid4().hex: random.random()}

        with patch.object(self.hub.analytics_engine, "load_data") as mock_load, \
             patch.object(self.hub.analytics_engine, "calculate_metrics", return_value=expected_metrics) as mock_calc:
            
            res = self.hub.get_realtime_metrics(symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            mock_calc.assert_called_once_with(symbol)
            self.assertEqual(res, expected_metrics)

    def test_evaluate_stream_performance(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        expected_perf = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.analytics_engine, "load_data") as mock_load, \
             patch.object(self.hub.analytics_engine, "evaluate_performance", return_value=expected_perf) as mock_eval:
            
            res = self.hub.evaluate_stream_performance(symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            mock_eval.assert_called_once_with(symbol)
            self.assertEqual(res, expected_perf)


class TestProcessRealtimeStreamHub(unittest.TestCase):

    def test_process_realtime_stream_hub_success(self):
        output_path = f"/var/log/{uuid.uuid4().hex}.log"
        storage_file = f"{uuid.uuid4().hex}.sqlite"
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        expected_metrics = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}

        with patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics") as mock_analytics_class:
            mock_analytics_instance = mock_analytics_class.return_value
            mock_analytics_instance.calculate_metrics.return_value = expected_metrics

            result = process_realtime_stream_hub(output_path, storage_file, symbol)

            mock_analytics_class.assert_called_once_with(storage_file)
            mock_analytics_instance.load_data.assert_called_once_with(storage_file)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(symbol)

            self.assertEqual(result["output_path"], output_path)
            self.assertEqual(result["storage_file"], storage_file)
            self.assertEqual(result["metrics"], expected_metrics)

    def test_process_realtime_stream_hub_exception(self):
        output_path = f"/var/log/{uuid.uuid4().hex}.log"
        storage_file = f"{uuid.uuid4().hex}.sqlite"
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))

        with patch("skills.market_portfolio_realtime_stream_analytics_hub.PortfolioPerformanceAnalytics") as mock_analytics_class:
            mock_analytics_instance = mock_analytics_class.return_value
            mock_analytics_instance.load_data.side_effect = Exception(uuid.uuid4().hex)

            result = process_realtime_stream_hub(output_path, storage_file, symbol)

            self.assertEqual(result["output_path"], output_path)
            self.assertEqual(result["storage_file"], storage_file)
            self.assertEqual(result["metrics"], {"symbol": symbol, "status": "initialized"})


if __name__ == "__main__":
    unittest.main()