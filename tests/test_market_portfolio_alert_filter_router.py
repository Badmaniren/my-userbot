import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_alert_filter_router import (
    AlertFilterRouter,
    route_and_filter_alerts
)


class TestAlertFilterRouter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = random.uniform(1.0, 100.0)
        self.channels = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

    def test_alert_filter_router_initialization(self):
        router = AlertFilterRouter(self.storage_file)
        self.assertEqual(router.storage_file, self.storage_file)
        self.assertIsNotNone(router)

    def test_route_and_filter_alerts_composition(self):
        mock_analytics_instance = MagicMock()
        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.uniform(-500.0, 500.0)
        mock_analytics_instance.evaluate_performance.return_value = {
            random_metric_key: random_metric_val,
            "status": "PASS"
        }
        mock_analytics_instance.calculate_metrics.return_value = {
            uuid.uuid4().hex: random.uniform(0.0, 10.0)
        }

        with patch('skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics', return_value=mock_analytics_instance) as mock_analytics_class, \
             patch('skills.market_portfolio_alert_filter_router.dispatch_portfolio_alerts') as mock_dispatch:

            router = AlertFilterRouter(self.storage_file)
            result = router.process_and_route(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels
            )

            mock_analytics_class.assert_called_once_with(self.storage_file)
            mock_analytics_instance.evaluate_performance.assert_called_once_with(self.symbol)
            mock_dispatch.assert_called_once()
            
            call_args = mock_dispatch.call_args[1]
            self.assertEqual(call_args['symbol'], self.symbol)
            self.assertEqual(call_args['url'], self.url)
            self.assertEqual(call_args['telegram_token'], self.token)
            self.assertEqual(call_args['chat_id'], self.chat_id)
            self.assertEqual(call_args['storage_file'], self.storage_file)
            self.assertEqual(call_args['severity_level'], self.severity_level)
            self.assertEqual(call_args['min_threshold'], self.min_threshold)
            self.assertEqual(call_args['channels'], self.channels)

            self.assertIn("dispatch_result", result)
            self.assertIn("analytics_data", result)
            self.assertEqual(result["analytics_data"]["status"], "PASS")

    def test_route_and_filter_alerts_helper_function(self):
        mock_router_instance = MagicMock()
        random_output_key = uuid.uuid4().hex
        random_output_val = uuid.uuid4().hex
        mock_router_instance.process_and_route.return_value = {
            random_output_key: random_output_val
        }

        with patch('skills.market_portfolio_alert_filter_router.AlertFilterRouter', return_value=mock_router_instance) as mock_class:
            res = route_and_filter_alerts(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels
            )

            mock_class.assert_called_once_with(self.storage_file)
            mock_router_instance.process_and_route.assert_called_once_with(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels
            )
            self.assertEqual(res[random_output_key], random_output_val)

    def test_filter_logic_suppresses_low_priority(self):
        mock_analytics_instance = MagicMock()
        mock_analytics_instance.evaluate_performance.return_value = {
            "score": -999.0,
            "status": "FAIL"
        }

        with patch('skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics', return_value=mock_analytics_instance), \
             patch('skills.market_portfolio_alert_filter_router.dispatch_portfolio_alerts') as mock_dispatch:

            router = AlertFilterRouter(self.storage_file)
            result = router.process_and_route(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id,
                severity_level="LOW",
                min_threshold=self.min_threshold,
                channels=self.channels
            )

            mock_dispatch.assert_not_called()
            self.assertEqual(result["analytics_data"]["status"], "FAIL")
            self.assertFalse(result.get("dispatched", True))

    def test_io_stream_mocking_chaos(self):
        random_bytes = uuid.uuid4().bytes
        stream_mock = io.BytesIO(random_bytes)
        
        with patch('skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics') as mock_analytics_class:
            mock_instance = mock_analytics_class.return_value
            mock_instance.load_data.return_value = stream_mock.read()

            router = AlertFilterRouter(self.storage_file)
            data = router.load_stream_data()
            
            self.assertEqual(data, random_bytes)


if __name__ == '__main__':
    unittest.main()