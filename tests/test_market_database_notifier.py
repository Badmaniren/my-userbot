import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
import string
from skills.market_database_notifier import MarketDatabaseNotifier


class TestMarketDatabaseNotifier(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.symbol = uuid.uuid4().hex[:5].upper()
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_initialization(self):
        notifier = MarketDatabaseNotifier(
            self.storage_file,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertEqual(notifier.storage_file, self.storage_file)
        self.assertEqual(notifier.telegram_token, self.telegram_token)
        self.assertEqual(notifier.chat_id, self.chat_id)
        self.assertIsNotNone(notifier.parser)

    def test_notify_on_fetch_composition_calls(self):
        with patch('skills.market_database_notifier.MarketParser.fetch_price', return_value=self.price) as mock_fetch_price, \
             patch('skills.market_database_notifier.MarketParser.fetch_and_store') as mock_fetch_and_store, \
             patch('skills.market_database_notifier.run_pipeline') as mock_run_pipeline:

            notifier = MarketDatabaseNotifier(
                self.storage_file,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            message = notifier.notify_on_fetch(self.symbol, self.url)

            mock_fetch_price.assert_called_once_with(self.url)
            mock_fetch_and_store.assert_called_once_with(self.symbol, self.price)
            mock_run_pipeline.assert_called_once_with(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file
            )

            self.assertIn(self.symbol, message)
            self.assertIn(str(self.price), message)
            self.assertIn(self.url, message)

    def test_notify_on_fetch_with_binary_mock_stream(self):
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        with patch('skills.market_database_notifier.MarketParser.fetch_price', return_value=self.price), \
             patch('skills.market_database_notifier.MarketParser.fetch_and_store'), \
             patch('skills.market_database_notifier.run_pipeline') as mock_run_pipeline, \
             patch('urllib.request.urlopen', return_value=mock_stream):

            notifier = MarketDatabaseNotifier(
                self.storage_file,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            res_message = notifier.notify_on_fetch(self.symbol, self.url)
            self.assertTrue(isinstance(res_message, str))
            self.assertTrue(mock_run_pipeline.called)

    def test_check_and_alert_without_symbol(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file, target_url=self.url)
        with patch.object(notifier.parser, 'parse_html_prices', return_value=self.price) as mock_parse:
            res = notifier.check_and_alert(symbol=None)
            mock_parse.assert_called_once_with(self.url)

    def test_check_and_alert_with_symbol(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file, target_url=self.url)
        with patch.object(notifier.parser, 'fetch_price', return_value=self.price), \
             patch.object(notifier.parser, 'fetch_and_store') as mock_store, \
             patch.object(notifier.parser, 'load_data', return_value=[f"{self.symbol},{self.price}\n"]):
            res = notifier.check_and_alert(symbol=self.symbol)
            mock_store.assert_called_once_with(self.symbol, self.price)
            self.assertEqual(res.get(self.symbol), self.price)

    def test_process_alert_full_args(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file)
        with patch.object(notifier.parser, 'fetch_and_store') as mock_store, \
             patch.object(notifier.parser, 'load_data', return_value=[f"{self.symbol},{self.price}\n"]):
            res = notifier.process_alert(symbol=self.symbol, target_url=self.url, price=self.price)
            mock_store.assert_called_once_with(self.symbol, self.price)
            self.assertEqual(res.get(self.symbol), self.price)

    def test_fetch_and_notify(self):
        notifier = MarketDatabaseNotifier(storage_file=self.storage_file)
        with patch.object(notifier.parser, 'fetch_and_store') as mock_store, \
             patch.object(notifier.parser, 'load_data', return_value=[f"{self.symbol},{self.price}\n"]):
            res = notifier.fetch_and_notify(self.symbol, self.url, self.price)
            mock_store.assert_called_once_with(self.symbol, self.price)
            self.assertEqual(res.get(self.symbol), self.price)


if __name__ == '__main__':
    unittest.main()
