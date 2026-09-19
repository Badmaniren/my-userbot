import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
from skills.market_database_notifier import MarketDatabaseNotifier

class TestMarketDatabaseNotifierInquisitor(unittest.TestCase):
    def setUp(self):
        self.rand_storage = f"db_{uuid.uuid4().hex}.json"
        self.rand_url = f"https://{uuid.uuid4().hex}.com/market"
        self.rand_symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.rand_price = round(random.uniform(10.0, 1500.0), 2)

        with patch('skills.db_storage.MarketParser') as mock_db, \
             patch('skills.market_parser.MarketParser') as mock_ext:
            self.mock_db_instance = mock_db.return_value
            self.mock_ext_instance = mock_ext.return_value
            self.notifier = MarketDatabaseNotifier(storage_file=self.rand_storage, target_url=self.rand_url)

    def test_init_and_aliases(self):
        self.assertEqual(self.notifier.storage_file, self.rand_storage)
        self.assertEqual(self.notifier.storage_path, self.rand_storage)
        self.assertEqual(self.notifier.target_url, self.rand_url)
        self.assertIsNotNone(self.notifier.db_storage)
        self.assertIsNotNone(self.notifier.market_parser)
        self.assertEqual(self.notifier.storage, self.notifier.db_storage)
        self.assertEqual(self.notifier.parser, self.notifier.market_parser)

    def test_check_and_alert_without_symbol(self):
        expected_result = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_ext_instance.parse_html_prices.return_value = expected_result

        res = self.notifier.check_and_alert(symbol=None)
        self.mock_ext_instance.parse_html_prices.assert_called_once_with(self.rand_url)
        self.assertEqual(res, expected_result)

    def test_check_and_alert_with_symbol(self):
        self.mock_ext_instance.fetch_price.return_value = self.rand_price
        expected_data = {self.rand_symbol: self.rand_price}
        self.mock_db_instance.load_data.return_value = expected_data

        res = self.notifier.check_and_alert(symbol=self.rand_symbol)

        self.mock_ext_instance.fetch_price.assert_called_once_with(self.rand_url)
        self.mock_db_instance.fetch_and_store.assert_called_once_with(self.rand_symbol, self.rand_price)
        self.mock_db_instance.load_data.assert_called_once_with(self.rand_storage)
        self.assertEqual(res, expected_data)

    def test_process_alert_full_args(self):
        alt_symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        alt_url = f"https://{uuid.uuid4().hex}.org"
        alt_price = round(random.uniform(1.0, 50.0), 2)
        expected_dict = {alt_symbol: alt_price}

        self.mock_db_instance.load_data.return_value = expected_dict

        res = self.notifier.process_alert(symbol=alt_symbol, target_url=alt_url, price=alt_price)

        self.mock_db_instance.fetch_and_store.assert_called_once_with(alt_symbol, alt_price)
        self.mock_db_instance.load_data.assert_called_once_with(self.rand_storage)
        self.assertEqual(res, expected_dict)

    def test_process_alert_only_symbol(self):
        with patch.object(self.notifier, 'check_and_alert') as mock_check:
            rand_res = {uuid.uuid4().hex: random.random()}
            mock_check.return_value = rand_res

            res = self.notifier.process_alert(symbol=self.rand_symbol)
            mock_check.assert_called_once_with(self.rand_symbol)
            self.assertEqual(res, rand_res)

    def test_process_alert_no_args(self):
        with patch.object(self.notifier, 'run_parsing_cycle') as mock_cycle:
            rand_res = {uuid.uuid4().hex: random.random()}
            mock_cycle.return_value = rand_res

            res = self.notifier.process_alert()
            mock_cycle.assert_called_once()
            self.assertEqual(res, rand_res)

    def test_run_parsing_cycle_with_url(self):
        parsed_data = {uuid.uuid4().hex: random.randint(100, 500)}
        self.mock_ext_instance.parse_html_prices.return_value = parsed_data

        res = self.notifier.run_parsing_cycle()
        self.mock_ext_instance.parse_html_prices.assert_called_once_with(self.rand_url)
        self.assertEqual(res, parsed_data)

    def test_run_parsing_cycle_no_url(self):
        notifier_empty = MarketDatabaseNotifier(storage_file=self.rand_storage, target_url=None)
        res = notifier_empty.run_parsing_cycle()
        self.assertEqual(res, {})

    def test_fetch_and_notify(self):
        expected_data = {self.rand_symbol: self.rand_price}
        self.mock_db_instance.load_data.return_value = expected_data

        res = self.notifier.fetch_and_notify(self.rand_symbol, self.rand_url, self.rand_price)

        self.mock_db_instance.fetch_and_store.assert_called_once_with(self.rand_symbol, self.rand_price)
        self.mock_db_instance.load_data.assert_called_once_with(self.rand_storage)
        self.assertEqual(res, expected_data)

    def test_stream_chaos_integration(self):
        methods = ['run_parsing_cycle']
        res = getattr(notifier_method := self.notifier, methods[0])() if methods else None
        self.assertIsInstance(res, dict)