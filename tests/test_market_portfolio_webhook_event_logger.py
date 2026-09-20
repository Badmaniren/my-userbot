import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io

from skills.market_portfolio_webhook_event_logger import MarketPortfolioWebhookEventLogger


class TestMarketPortfolioWebhookEventLogger(unittest.TestCase):

    def test_log_webhook_event_success(self):
        rand_storage = f"storage_{uuid.uuid4().hex}.json"
        rand_webhook_url = f"https://{uuid.uuid4().hex}.com/hook"
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        rand_export_url = f"https://{uuid.uuid4().hex}.com/export"
        rand_shifts = [random.randint(1, 5), random.randint(6, 10)]
        expected_export_result = {uuid.uuid4().hex: random.randint(100, 500)}

        with patch("skills.market_portfolio_webhook_event_logger.MarketPortfolioWebhookSync") as mock_sync_cls, \
             patch("skills.market_portfolio_webhook_event_logger.PortfolioDataExporter") as mock_exporter_cls:

            mock_sync_instance = mock_sync_cls.return_value
            mock_sync_instance.trigger_webhook_sync.return_value = True

            mock_exporter_instance = mock_exporter_cls.return_value
            mock_exporter_instance.export_all.return_value = expected_export_result

            logger = MarketPortfolioWebhookEventLogger(rand_storage, rand_webhook_url)
            result = logger.log_and_sync_event(rand_symbol, rand_price, rand_export_url, rand_shifts)

            mock_sync_cls.assert_called_once_with(rand_storage, rand_webhook_url)
            mock_sync_instance.trigger_webhook_sync.assert_called_once_with(rand_symbol, rand_price)

            mock_exporter_cls.assert_called_once_with(rand_storage)
            mock_exporter_instance.export_all.assert_called_once_with(rand_export_url, rand_symbol, rand_shifts)

            self.assertIn("sync_success", result)
            self.assertTrue(result["sync_success"])
            self.assertEqual(result["export_data"], expected_export_result)
            self.assertEqual(result["symbol"], rand_symbol)
            self.assertEqual(result["price"], rand_price)

    def test_log_webhook_event_sync_failure(self):
        rand_storage = f"data_{uuid.uuid4().hex}.json"
        rand_webhook_url = f"http://{uuid.uuid4().hex}.net/webhook"
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_price = round(random.uniform(1.0, 50.0), 2)
        rand_export_url = f"http://{uuid.uuid4().hex}.net/api"
        rand_shifts = [random.randint(1, 3)]

        with patch("skills.market_portfolio_webhook_event_logger.MarketPortfolioWebhookSync") as mock_sync_cls, \
             patch("skills.market_portfolio_webhook_event_logger.PortfolioDataExporter") as mock_exporter_cls:

            mock_sync_instance = mock_sync_cls.return_value
            mock_sync_instance.trigger_webhook_sync.return_value = False

            mock_exporter_instance = mock_exporter_cls.return_value
            mock_exporter_instance.export_all.return_value = {}

            logger = MarketPortfolioWebhookEventLogger(rand_storage, rand_webhook_url)
            result = logger.log_and_sync_event(rand_symbol, rand_price, rand_export_url, rand_shifts)

            self.assertIn("sync_success", result)
            self.assertFalse(result["sync_success"])
            mock_exporter_instance.export_all.assert_not_called()

    def test_stream_event_export(self):
        rand_storage = f"file_{uuid.uuid4().hex}.db"
        rand_webhook_url = f"https://{uuid.uuid4().hex}.org/hook"
        rand_bytes_content = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.market_portfolio_webhook_event_logger.MarketPortfolioWebhookSync") as mock_sync_cls, \
             patch("skills.market_portfolio_webhook_event_logger.PortfolioDataExporter") as mock_exporter_cls:

            mock_exporter_instance = mock_exporter_cls.return_value
            mock_exporter_instance.export_stream.return_value = io.BytesIO(rand_bytes_content)

            logger = MarketPortfolioWebhookEventLogger(rand_storage, rand_webhook_url)
            stream_result = logger.get_event_stream()

            mock_exporter_cls.assert_called_once_with(rand_storage)
            mock_exporter_instance.export_stream.assert_called_once()
            self.assertEqual(stream_result.read(), rand_bytes_content)


if __name__ == "__main__":
    unittest.main()