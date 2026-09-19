import unittest
import uuid
import random
import os
import requests
from unittest.mock import patch
from skills import telegram_alert
from skills import db_storage

class TestTelegramAlertIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.symbol = f"COIN_{self.test_id}"
        self.db_filename = f"test_market_data_{self.test_id}.json"
        
        # Переопределяем файл БД в модуле db_storage, чтобы тест был изощренным и реальным
        if hasattr(db_storage, 'MarketParser'):
            self.original_parser = db_storage.MarketParser
            # Патчим или настраиваем реальное хранилище, если поддерживается
            
    def tearDown(self):
        if os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except OSError:
                pass

    @patch('skills.market_parser.fetch_price')
    @patch('requests.post')
    def techno_integration_test(self, mock_requests_post, mock_fetch_price):
        random_price = float(round(random.uniform(100.0, 2000.0), 2))
        threshold = random_price - 10.0
        chat_id = f"chat_{self.test_id}"
        token = f"token_{self.test_id}"
        url = f"https://example.com/price/{self.test_id}"

        mock_fetch_price.return_value = random_price
        mock_requests_post.return_value.status_code = 200

        result = telegram_alert.check_and_alert(
            symbol=self.symbol,
            url=url,
            threshold=threshold,
            chat_id=chat_id,
            token=token
        )

        self.assertTrue(result, "Функция должна вернуть True, так как цена выше порога")
        mock_fetch_price.assert_called_once_with(url)
        
        mock_requests_post.assert_called_once()
        called_args, called_kwargs = mock_requests_post.call_args
        
        expected_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.assertEqual(called_args[0], expected_api_url)
        
        payload = called_kwargs.get('json')
        self.assertIsNotNone(payload)
        self.assertEqual(payload['chat_id'], chat_id)
        self.assertIn(self.symbol, payload['text'])
        self.assertIn(str(random_price), payload['text'])

    @patch('skills.market_parser.fetch_price')
    @patch('requests.post')
    def test_threshold_not_reached(self, mock_requests_post, mock_fetch_price):
        random_price = float(round(random.uniform(10.0, 50.0), 2))
        threshold = random_price + 100.0
        url = f"https://example.com/price/{self.test_id}"

        mock_fetch_price.return_value = random_price

        result = telegram_alert.check_and_alert(
            symbol=self.symbol,
            url=url,
            threshold=threshold
        )

        self.assertFalse(result, "Функция должна вернуть False, так как цена ниже порога")
        mock_requests_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()