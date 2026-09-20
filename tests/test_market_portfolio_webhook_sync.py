import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.market_portfolio_webhook_sync import start_new

class TestMarketPortfolioWebhookSync(unittest.TestCase):

    def setUp(self):
        self.random_prefix = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.storage_file = f"{self_storage_file_gen()}"
        self.url = f"https://{uuid.uuid4().hex}.com/{random.randint(100, 999)}"
        self.symbol = uuid.uuid4().hex[:6].upper()
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 5000.0), 2)
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.shift = round(random.uniform(-5.0, 5.0), 2)

    def test_start_new_execution_flow(self):
        dynamic_message = f"alert_{uuid.uuid4().hex}"
        dynamic_payload = {
            "symbol": self.symbol,
            "price": self.price,
            "url": self.url,
            "token": self.token,
            "chat_id": self.chat_id,
            "threshold": self.threshold,
            "shift": self.shift,
            "storage": self.storage_file,
            "msg": dynamic_message
        }

        with patch('skills.market_portfolio_webhook_sync.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_webhook_sync.AutonomousSentinel') as mock_sentinel_cls, \
             patch('skills.market_portfolio_webhook_sync.MarketPortfolioIntegrationHub') as mock_hub_cls, \
             patch('skills.market_portfolio_webhook_sync.send_telegram_notification') as mock_send_tg:

            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = self.price
            mock_parser.parse_html_prices.return_value = [self.price]

            mock_sentinel = mock_sentinel_cls.return_value
            mock_sentinel.run_surveillance.return_value = True

            mock_hub = mock_hub_cls.return_value
            mock_hub.run_integrated_pipeline.return_value = dynamic_payload

            mock_send_tg.return_value = True

            result = start_new(
                storage_file=self.storage_file,
                url=self.url,
                symbol=self.symbol,
                telegram_token=self.token,
                chat_id=self.chat_id,
                threshold=self.threshold,
                shift=self.shift
            )

            mock_parser_cls.assert_called_once_with(self.storage_file)
            mock_parser.fetch_price.assert_called_once_with(self.url)
            mock_sentinel_cls.assert_called_once_with(self.storage_file, self.threshold)
            mock_sentinel.run_surveillance.assert_called_once_with(self.symbol, self.url, self.token, self.chat_id)
            mock_hub_cls.assert_called_once_with(self.storage_file)
            mock_hub.run_integrated_pipeline.assert_called_once_with(
                url=self.url,
                symbol=self.symbol,
                shifts=self.shift,
                telegram_token=self.token,
                chat_id=self.chat_id
            )
            self.assertIsNotNone(result)

    def test_start_new_handles_exceptions_gracefully(self):
        err_message = f"critical_fail_{uuid.uuid4().hex}"
        
        with patch('skills.market_portfolio_webhook_sync.MarketParser', side_effect=Exception(err_message)):
            with self.assertRaises(Exception) as ctx:
                start_new(
                    storage_file=self.storage_file,
                    url=self.url,
                    symbol=self.symbol,
                    telegram_token=self.token,
                    chat_id=self.chat_id,
                    threshold=self.threshold,
                    shift=self.shift
                )
            self.assertIn(err_message, str(ctx.exception))

    def test_start_new_stream_io_integrity(self):
        stream_data = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        with patch('skills.market_portfolio_webhook_sync.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_webhook_sync.AutonomousSentinel') as mock_sentinel_cls, \
             patch('skills.market_portfolio_webhook_sync.MarketPortfolioIntegrationHub') as mock_hub_cls:

            mock_parser = mock_parser_cls.return_value
            mock_parser.load_data.return_value = mock_stream.read()

            result = start_new(
                storage_file=self.storage_file,
                url=self.url,
                symbol=self.symbol,
                telegram_token=self.token,
                chat_id=self.chat_id,
                threshold=self.threshold,
                shift=self.shift
            )

            mock_parser.load_data.assert_called()


def self_storage_file_gen():
    return f"{uuid.uuid4().hex}.json"


if __name__ == '__main__':
    unittest.main()