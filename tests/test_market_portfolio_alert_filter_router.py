import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_alert_filter_router import (
    AlertFilterRouter,
    route_and_filter_alerts,
    filter_and_route_portfolio_alerts,
    process_alert_filter_routing
)


class TestAlertFilterRouter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000, 999999))
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = [uuid.uuid4().hex, uuid.uuid4().hex]

    @patch("skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_alert_filter_router.dispatch_portfolio_alerts")
    def test_process_and_route_low_severity_fail(self, mock_dispatch, mock_analytics_class):
        mock_analytics_instance = mock_analytics_class.return_value
        unique_status = "FAIL"
        mock_analytics_instance.evaluate_performance.return_value = {
            "status": unique_status,
            "metric_id": uuid.uuid4().hex
        }

        router = AlertFilterRouter(self.storage_file)
        result = router.process_and_route(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level="LOW",
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertFalse(result["dispatched"])
        self.assertEqual(result["analytics_data"]["status"], unique_status)
        mock_dispatch.assert_not_called()

    @patch("skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics")
    @patch("skills.market_portfolio_alert_filter_router.dispatch_portfolio_alerts")
    def test_process_and_route_success_dispatch(self, mock_dispatch, mock_analytics_class):
        mock_analytics_instance = mock_analytics_class.return_value
        unique_status = uuid.uuid4().hex
        mock_analytics_instance.evaluate_performance.return_value = {
            "status": unique_status,
            "data_key": uuid.uuid4().hex
        }
        dispatch_marker = {"dispatched": True, "id": uuid.uuid4().hex}
        mock_dispatch.return_value = dispatch_marker

        router = AlertFilterRouter(self.storage_file)
        result = router.process_and_route(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level="HIGH",
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result["dispatch_result"], dispatch_marker)
        self.assertEqual(result["status"], unique_status)
        mock_dispatch.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold=self.min_threshold,
            channels=self.channels
        )

    @patch("skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics")
    def test_load_stream_data_with_load_data_method(self, mock_analytics_class):
        mock_analytics_instance = mock_analytics_class.return_value
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_analytics_instance.load_data.return_value = expected_data

        router = AlertFilterRouter(self.storage_file)
        data = router.load_stream_data()

        self.assertEqual(data, expected_data)
        mock_analytics_instance.load_data.assert_called_once()

    @patch("skills.market_portfolio_alert_filter_router.PortfolioPerformanceAnalytics")
    def test_load_stream_data_fallback_to_file(self, mock_analytics_class):
        mock_analytics_instance = mock_analytics_class.return_value
        del mock_analytics_instance.load_data

        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_file = io.BytesIO(random_bytes)

        router = AlertFilterRouter(self.storage_file)
        with patch("builtins.open", return_value=mock_file) as mock_open:
            data = router.load_stream_data()
            mock_open.assert_called_once_with(self.storage_file, "rb")
            self.assertEqual(data, random_bytes)

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.process_and_route")
    def test_route_filtered_alerts_delegation(self, mock_process_and_route):
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_process_and_route.return_value = expected_return

        router = AlertFilterRouter(self.storage_file)
        result = router.route_filtered_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result, expected_return)
        mock_process_and_route.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.process_and_route")
    def test_route_and_filter_alerts_helper(self, mock_process_and_route):
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_process_and_route.return_value = expected_return

        result = route_and_filter_alerts(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result, expected_return)

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.process_and_route")
    def test_filter_and_route_portfolio_alerts_helper(self, mock_process_and_route):
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_process_and_route.return_value = expected_return

        result = filter_and_route_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result, expected_return)

    @patch("skills.market_portfolio_alert_filter_router.AlertFilterRouter.process_and_route")
    def test_process_alert_filter_routing_helper(self, mock_process_and_route):
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_process_and_route.return_value = expected_return

        result = process_alert_filter_routing(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result, expected_return)


if __name__ == "__main__":
    unittest.main()