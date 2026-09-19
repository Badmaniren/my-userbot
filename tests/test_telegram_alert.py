import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

market_parser_stub = types.ModuleType('skills.market_parser')
market_parser_stub.MarketParser = MagicMock()
market_parser_stub.fetch_price = MagicMock()
market_parser_stub.parse_html_prices = MagicMock()
market_parser_stub.fetch_and_store = MagicMock()
market_parser_stub.load_data = MagicMock()

db_storage_stub = types.ModuleType('skills.db_storage')
db_storage_stub.MarketParser = MagicMock()
db_storage_stub.fetch_price = MagicMock()
db_storage_stub.parse_html_prices = MagicMock()
db_storage_stub.fetch_and_store = MagicMock()
db_storage_stub.load_data = MagicMock()

sys.modules['skills.market_parser'] = market_parser_stub
sys.modules['skills.db_storage'] = db_storage_stub

from skills import telegram_alert


class TestTelegramAlertComposition(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_price = round(random.uniform(10.0, 1000.0), 2)
        self.rand_threshold = round(random.uniform(5.0, 2000.0), 2)
        self.rand_token = uuid.uuid4().hex

    def test_telegram_alert_composition_imports(self):
        self.assertTrue(hasattr(telegram_alert, 'market_parser') or 'market_parser' in telegram_alert.__globals__.get('', {}),
                        "Модуль telegram_alert обязан импортировать market_parser")
        self.assertTrue(hasattr(telegram_alert, 'db_storage') or 'db_storage' in telegram_alert.__globals__.get('', {}),
                        "Модуль telegram_alert обязан импортировать db_storage")

    @patch('skills.telegram_alert.requests.post')
    def test_check_and_alert_triggers(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch('skills.market_parser.fetch_price', return_value=self.rand_price) as mock_fetch, \
             patch('skills.db_storage.fetch_and_store') as mock_store:

            if hasattr(telegram_alert, 'check_and_alert'):
                try:
                    telegram_alert.check_and_alert(
                        symbol=self.rand_symbol,
                        url=self.rand_url,
                        threshold=self.rand_price - 10.0,
                        chat_id=self.rand_chat_id,
                        token=self.rand_token
                    )
                except TypeError:
                    telegram_alert.check_and_alert(self.rand_symbol, self.rand_url, self.rand_price - 10.0)

                mock_fetch.assert_called_once()
                mock_store.assert_called()
                mock_post.assert_called_once()
                
                called_args, called_kwargs = mock_post.call_args
                payload = called_kwargs.get('json', {})
                if not payload and len(called_args) > 1:
                    payload = called_args[1]
                
                self.assertTrue(
                    any(self.rand_symbol in str(val) for val in payload.values()) or
                    any(str(self.rand_price) in str(val) for val in payload.values()),
                    "Уведомление в Telegram должно содержать данные цены или символа"
                )

    @patch('skills.telegram_alert.requests.post')
    def test_check_and_alert_below_threshold(self, mock_post):
        with patch('skills.market_parser.fetch_price', return_value=self.rand_price) as mock_fetch, \
             patch('skills.db_storage.fetch_and_store') as mock_store:

            if hasattr(telegram_alert, 'check_and_alert'):
                try:
                    telegram_alert.check_and_alert(
                        symbol=self.rand_symbol,
                        url=self.rand_url,
                        threshold=self.rand_price + 100.0,
                        chat_id=self.rand_chat_id,
                        token=self.rand_token
                    )
                except TypeError:
                    pass

                mock_fetch.assert_called_once()
                mock_post.assert_not_called()

    def test_stream_processing_with_io(self):
        stream_data = f"{uuid.uuid4().hex},{random.randint(1, 500)}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        if hasattr(telegram_alert, 'process_stream_alert'):
            with patch('skills.market_parser.parse_html_prices') as mock_parse:
                mock_parse.return_value = stream_data.decode('utf-8')
                res = telegram_alert.process_stream_alert(mock_stream, uuid.uuid4().hex)
                self.assertIsNotNone(res)


if __name__ == '__main__':
    unittest.main()