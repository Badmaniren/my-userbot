import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.telegram_alert import check_and_alert, process_stream_alert, TelegramAlertService

class TestTelegramAlert(unittest.TestCase):

    @patch('skills.telegram_alert.requests.post')
    @patch('skills.telegram_alert.db_storage.fetch_and_store')
    @patch('skills.telegram_alert.market_parser.fetch_price')
    def test_check_and_alert_success(self, mock_fetch_price, mock_db_store, mock_requests_post):
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        url = f"https://{uuid.uuid4().hex}.com"
        threshold = random.uniform(10.0, 50.0)
        price = threshold + random.uniform(1.0, 10.0)
        chat_id = str(random.randint(1000, 9999))
        token = uuid.uuid4().hex

        mock_fetch_price.return_value = price
        mock_response = MagicMock()
        mock_requests_post.return_value = mock_response

        result = check_and_alert(symbol, url, threshold, chat_id=chat_id, token=token)

        self.assertTrue(result)
        mock_fetch_price.assert_called_once_with(url)
        mock_db_store.assert_called_once_with(symbol, price)
        mock_requests_post.assert_called_once()
        
        args, kwargs = mock_requests_post.call_args
        self.assertIn(token, args[0])
        self.assertEqual(kwargs["json"]["chat_id"], chat_id)
        self.assertIn(symbol, kwargs["json"]["text"])

    @patch('skills.telegram_alert.requests.post')
    @patch('skills.telegram_alert.db_storage.fetch_and_store')
    @patch('skills.telegram_alert.market_parser.fetch_price')
    def test_check_and_alert_below_threshold(self, mock_fetch_price, mock_db_store, mock_requests_post):
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        url = f"https://{uuid.uuid4().hex}.com"
        threshold = random.uniform(50.0, 100.0)
        price = threshold - random.uniform(1.0, 10.0)

        mock_fetch_price.return_value = price

        result = check_and_alert(symbol, url, threshold)

        self.assertFalse(result)
        mock_fetch_price.assert_called_once_with(url)
        mock_db_store.assert_called_once_with(symbol, price)
        mock_requests_post.assert_not_called()

    @patch('skills.telegram_alert.market_parser.parse_html_prices')
    def test_process_stream_alert(self, mock_parse_html):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_bytes)
        expected_parsed = {uuid.uuid4().hex: random.uniform(1.0, 100.0)}
        mock_parse_html.return_value = expected_parsed

        token = uuid.uuid4().hex
        result = process_stream_alert(stream, token=token)

        self.assertEqual(result, expected_parsed)
        mock_parse_html.assert_called_once_with(random_bytes)

    @patch('skills.telegram_alert.requests.post')
    def test_telegram_alert_service_method(self, mock_requests_post):
        mock_parser = MagicMock()
        mock_db = MagicMock()
        
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        url = f"https://{uuid.uuid4().hex}.org"
        threshold = random.uniform(20.0, 40.0)
        price = threshold + 5.0
        chat_id = str(random.randint(100, 999))
        token = uuid.uuid4().hex

        mock_parser.fetch_price.return_value = price

        service = TelegramAlertService(db_storage=mock_db, market_parser=mock_parser)
        result = service.check_and_alert(symbol, threshold, chat_id=chat_id, token=token, url=url)

        self.assertTrue(result)
        mock_parser.fetch_price.assert_called_once_with(url)
        mock_db.fetch_and_store.assert_called_once_with(symbol, price)
        mock_requests_post.assert_called_once()
        
        _, kwargs = mock_requests_post.call_args
        self.assertEqual(kwargs["json"]["chat_id"], chat_id)

    @patch('skills.telegram_alert.requests.post')
    @patch('skills.telegram_alert.db_storage.fetch_and_store')
    @patch('skills.telegram_alert.market_parser.fetch_price')
    def test_telegram_alert_service_default_dependencies(self, mock_fetch_price, mock_db_store, mock_requests_post):
        mock_parser = None
        mock_db = None
        
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        threshold = random.uniform(10.0, 20.0)
        price = threshold - 2.0

        mock_fetch_price.return_value = price

        service = TelegramAlertService(db_storage=mock_db, market_parser=mock_parser)
        result = service.check_and_alert(symbol, threshold)

        self.assertFalse(result)
        mock_fetch_price.assert_called_once()
        mock_db_store.assert_called_once_with(symbol, price)
        mock_requests_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()