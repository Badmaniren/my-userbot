import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_notifier import MarketNotifier
from skills import market_parser, db_storage


class TestMarketNotifier(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/market"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)
        self.storage_filename = f"{uuid.uuid4().hex}.json"

    def test_composition_initialization(self):
        with patch('skills.market_notifier.MarketParser') as mock_parser_cls, \
             patch('skills.market_notifier.MarketStorage') as mock_storage_cls:

            notifier = MarketNotifier(self.storage_filename)
            
            mock_parser_cls.assert_called_once()
            mock_storage_cls.assert_called_once_with(self.storage_filename)
            self.assertIsNotNone(notifier.parser)
            self.assertIsNotNone(notifier.storage)

    def test_fetch_and_notify_success(self):
        with patch('skills.market_notifier.MarketParser') as mock_parser_cls, \
             patch('skills.market_notifier.MarketStorage') as mock_storage_cls:

            mock_parser_instance = mock_parser_cls.return_value
            mock_storage_instance = mock_storage_cls.return_value

            mock_parser_instance.fetch_price.return_value = self.random_price
            mock_storage_instance.fetch_and_store.return_value = True

            notifier = MarketNotifier(self.storage_filename)
            result = notifier.process_and_notify(self.random_symbol, self.random_url)

            mock_parser_instance.fetch_price.assert_called_once_with(self.random_url)
            mock_storage_instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)
            self.assertTrue(result)

    def test_fetch_and_notify_failure_on_fetch(self):
        with patch('skills.market_notifier.MarketParser') as mock_parser_cls, \
             patch('skills.market_notifier.MarketStorage') as mock_storage_cls:

            mock_parser_instance = mock_parser_cls.return_value
            mock_storage_instance = mock_storage_cls.return_value

            mock_parser_instance.fetch_price.side_effect = Exception(uuid.uuid4().hex)

            notifier = MarketNotifier(self.storage_filename)
            result = notifier.process_and_notify(self.random_symbol, self.random_url)

            mock_parser_instance.fetch_price.assert_called_once_with(self.random_url)
            mock_storage_instance.fetch_and_store.assert_not_called()
            self.assertFalse(result)

    def test_load_historical_data_io_stream(self):
        random_bytes = uuid.uuid4().bytes
        mock_file_stream = io.BytesIO(random_bytes)

        with patch('skills.market_notifier.MarketParser') as mock_parser_cls, \
             patch('skills.market_notifier.MarketStorage') as mock_storage_cls:

            mock_storage_instance = mock_storage_cls.return_value
            mock_storage_instance.load_data.return_value = mock_file_stream

            notifier = MarketNotifier(self.storage_filename)
            data = notifier.get_historical_data(self.storage_filename)

            mock_storage_instance.load_data.assert_called_once_with(self.storage_filename)
            self.assertEqual(data.read(), random_bytes)


if __name__ == '__main__':
    unittest.main()