import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_report_generator import MarketReportGenerator, generate_market_report


class TestMarketReportGenerator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.generator = MarketReportGenerator(self.storage_file)

    def test_generate_symbol_report_list_data(self):
        min_p = round(random.uniform(1.0, 50.0), 2)
        max_p = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": min_p},
            {"symbol": self.symbol, "price": max_p},
            {"symbol": "OTHER", "price": 999.0}
        ]

        with patch.object(self.generator.parser, 'load_data', return_value=mock_data) as mock_load:
            res = self.generator.generate_symbol_report(self.symbol)
            mock_load.assert_called_once_with(self.storage_file)
            self.assertTrue(res.get(self.symbol))
            self.assertEqual(res['count'], 2)
            self.assertEqual(res['min_price'], min_p)
            self.assertEqual(res['max_price'], max_p)

    def test_generate_symbol_report_dict_data(self):
        target_price = round(random.uniform(10.0, 500.0), 2)
        mock_data = {
            self.symbol: target_price,
            f"OTHER_{uuid.uuid4().hex[:4]}": 123.45
        }

        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            res = self.generator.generate_symbol_report(self.symbol)
            self.assertTrue(res.get(self.symbol))
            self.assertEqual(res['count'], 1)
            self.assertEqual(res['min_price'], target_price)
            self.assertEqual(res['max_price'], target_price)

    def test_generate_symbol_report_no_data(self):
        with patch.object(self.generator.parser, 'load_data', return_value=None):
            res = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(res['count'], 0)
            self.assertIn('error', res)

    def test_generate_symbol_report_no_prices(self):
        mock_data = [{"symbol": self.symbol}]
        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            res = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(res['count'], 0)
            self.assertIn('error', res)

    def test_update_and_fetch_report(self):
        expected_price = round(random.uniform(100.0, 999.99), 2)

        with patch.object(self.generator.parser, 'fetch_price', return_value=expected_price) as mock_fetch, \
             patch.object(self.generator.parser, 'fetch_and_store') as mock_store:
            
            price = self.generator.update_and_fetch_report(self.url, self.symbol)
            
            mock_fetch.assert_called_once_with(self.url)
            mock_store.assert_called_once_with(self.symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_get_raw_stream_dump(self):
        mock_dump = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch.object(self.generator.parser, 'load_data', return_value=mock_dump) as mock_load:
            dump = self.generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(dump, mock_dump)

    def test_generate_market_report_function(self):
        target_price = round(random.uniform(5.0, 50.0), 2)
        mock_db_data = {self.symbol: target_price}

        with patch('skills.market_report_generator.db_storage') as mock_db:
            mock_db.load_data = MagicMock(return_value=mock_db_data)
            if hasattr(mock_db, 'load_db'):
                delattr(mock_db, 'load_db')

            report_str = generate_market_report(self.storage_file, self.symbol)
            mock_db.load_data.assert_called_once_with(self.storage_file)
            self.assertIn(self.symbol, report_str)
            self.assertIn(str(target_price), report_str)

    def test_generate_market_report_fallback_load_db(self):
        target_price = round(random.uniform(50.0, 150.0), 2)
        mock_db_data = {self.symbol: target_price}

        with patch('skills.market_report_generator.db_storage') as mock_db:
            if hasattr(mock_db, 'load_data'):
                delattr(mock_db, 'load_data')
            mock_db.load_db = MagicMock(return_value=mock_db_data)

            report_str = generate_market_report(self.storage_file, self.symbol)
            mock_db.load_db.assert_called_once_with(self.storage_file)
            self.assertIn(self.symbol, report_str)
            self.assertIn(str(target_price), report_str)


if __name__ == '__main__':
    unittest.main()