import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_notifier import MarketNotifier


class TestMarketNotifier(unittest.TestCase):

    def setUp(self):
        self.random_storage_file = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/api/price"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_filename = f"{uuid.uuid4().hex}_history.json"

    @patch('skills.market_notifier.MarketStorage')
    @patch('skills.market_notifier.MarketParser')
    def test_process_and_notify_with_price_provided(self, mock_parser_class, mock_storage_class):
        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.fetch_and_store.return_value = True

        notifier = MarketNotifier(self.random_storage_file)
        result = notifier.process_and_notify(self.random_symbol, price=self.random_price)

        self.assertTrue(result)
        mock_parser_class.return_value.fetch_price.assert_not_called()
        mock_storage_instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)

    @patch('skills.market_notifier.MarketStorage')
    @patch('skills.market_notifier.MarketParser')
    def test_process_and_notify_fetches_price_via_url(self, mock_parser_class, mock_storage_class):
        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.return_value = self.random_price

        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.fetch_and_store.return_value = True

        notifier = MarketNotifier(self.random_storage_file)
        result = notifier.process_and_notify(self.random_symbol, url=self.random_url)

        self.assertTrue(result)
        mock_parser_instance.fetch_price.assert_called_once_with(self.random_url)
        mock_storage_instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)

    @patch('skills.market_notifier.MarketStorage')
    @patch('skills.market_notifier.MarketParser')
    def test_process_and_notify_missing_price_and_url_returns_false(self, mock_parser_class, mock_storage_class):
        notifier = MarketNotifier(self.random_storage_file)
        result = notifier.process_and_notify(self.random_symbol)

        self.assertFalse(result)
        mock_parser_class.return_value.fetch_price.assert_not_called()
        mock_storage_class.return_value.fetch_and_store.assert_not_called()

    @patch('skills.market_notifier.MarketStorage')
    @patch('skills.market_notifier.MarketParser')
    def test_get_historical_data_uses_default_filename(self, mock_parser_class, mock_storage_class):
        mock_data = [{uuid.uuid4().hex: random.randint(1, 100)}]
        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.load_data.return_value = mock_data

        notifier = MarketNotifier(self.random_storage_file)
        data = notifier.get_historical_data()

        self.assertEqual(data, mock_data)
        mock_storage_instance.load_data.assert_called_once_with(self.random_storage_file)

    @patch('skills.market_notifier.MarketStorage')
    @patch('skills.market_notifier.MarketParser')
    def test_get_historical_data_uses_custom_filename(self, mock_parser_class, mock_storage_class):
        mock_data = [{uuid.uuid4().hex: random.randint(101, 200)}]
        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.load_data.return_value = mock_data

        notifier = MarketNotifier(self.random_storage_file)
        data = notifier.get_historical_data(self.random_filename)

        self.assertEqual(data, mock_data)
        mock_storage_instance.load_data.assert_called_once_with(self.random_filename)


if __name__ == '__main__':
    unittest.main()