import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_alert_sender import MarketAlertSender
import skills.market_parser as mp_module
import skills.db_storage as db_module


class TestMarketAlertSender(unittest.TestCase):

    def setUp(self):
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_storage = f"{uuid.uuid4().hex}.json"

        self.threshold_low = round(random.uniform(10.0, 50.0), 2)
        self.threshold_high = round(random.uniform(100.0, 500.0), 2)
        self.current_price = round(random.uniform(5.0, 600.0), 2)

    def test_init_composition(self):
        with patch('skills.market_alert_sender.MarketParser') as mock_parser_cls, \
             patch('skills.market_alert_sender.DbStorage') as mock_storage_cls:

            sender = MarketAlertSender(self.random_storage)

            mock_parser_cls.assert_called_once()
            mock_storage_cls.assert_called_once_with(self.random_storage)
            self.assertIsNotNone(sender.parser)
            self.assertIsNotNone(sender.storage)

    def test_check_and_alert_below_threshold(self):
        price_below = self.threshold_low - random.uniform(1.0, 5.0)

        with patch('skills.market_alert_sender.MarketParser') as mock_parser_cls, \
             patch('skills.market_alert_sender.DbStorage') as mock_storage_cls:

            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = price_below

            mock_storage = mock_storage_cls.return_value

            sender = MarketAlertSender(self.random_storage)
            alert = sender.check_and_alert(self.random_url, self.random_symbol, self.threshold_low, self.threshold_high)

            mock_parser.fetch_price.assert_called_once_with(self.random_url)
            mock_storage.fetch_and_store.assert_called_once_with(self.random_symbol, price_below)

            self.assertIsNotNone(alert)
            self.assertIn(self.random_symbol, str(alert))
            self.assertIn(str(price_below), str(alert))

    def test_check_and_alert_above_threshold(self):
        price_above = self.threshold_high + random.uniform(1.0, 5.0)

        with patch('skills.market_alert_sender.MarketParser') as mock_parser_cls, \
             patch('skills.market_alert_sender.DbStorage') as mock_storage_cls:

            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = price_above

            mock_storage = mock_storage_cls.return_value

            sender = MarketAlertSender(self.random_storage)
            alert = sender.check_and_alert(self.random_url, self.random_symbol, self.threshold_low, self.threshold_high)

            mock_parser.fetch_price.assert_called_once_with(self.random_url)
            mock_storage.fetch_and_store.assert_called_once_with(self.random_symbol, price_above)

            self.assertIsNotNone(alert)

    def test_check_and_alert_normal_range(self):
        price_normal = (self.threshold_low + self.threshold_high) / 2.0

        with patch('skills.market_alert_sender.MarketParser') as mock_parser_cls, \
             patch('skills.market_alert_sender.DbStorage') as mock_storage_cls:

            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = price_normal

            mock_storage = mock_storage_cls.return_value

            sender = MarketAlertSender(self.random_storage)
            alert = sender.check_and_alert(self.random_url, self.random_symbol, self.threshold_low, self.threshold_high)

            mock_parser.fetch_price.assert_called_once_with(self.random_url)
            mock_storage.fetch_and_store.assert_not_called()

            self.assertIsNone(alert)

    def test_parser_and_storage_integration(self):
        random_bytes = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('skills.market_alert_sender.MarketParser') as mock_parser_cls, \
             patch('skills.market_alert_sender.DbStorage') as mock_storage_cls:

            mock_parser = mock_parser_cls.return_value
            mock_parser.fetch_price.return_value = self.current_price

            mock_storage = mock_storage_cls.return_value
            mock_storage.load_data.return_value = {self.random_symbol: self.current_price}

            sender = MarketAlertSender(self.random_storage)

            fetched = sender.parser.fetch_price(self.random_url)
            sender.storage.fetch_and_store(self.random_symbol, fetched)
            data = sender.storage.load_data(self.random_storage)

            self.assertEqual(fetched, self.current_raisers if hasattr(self, 'current_raisers') else self.current_price)
            self.assertEqual(data[self.random_symbol], self.current_price)


if __name__ == '__main__':
    unittest.main()