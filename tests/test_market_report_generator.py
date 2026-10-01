import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.generator = MarketReportGenerator(storage_file=self.storage_file)

    def test_generate_symbol_report_list_data(self):
        min_p = round(random.uniform(10.0, 50.0), 2)
        max_p = round(random.uniform(51.0, 100.0), 2)
        
        mock_data = [
            {"symbol": self.symbol, "price": min_p},
            {"symbol": self.symbol, "price": max_p},
            {"symbol": "".join(random.choices(string.ascii_uppercase, k=4)), "price": 999.9}
        ]

        with patch.object(self.generator.parser, 'load_data', return_value=mock_data) as mock_load:
            report = self.generator.generate_symbol_report(self.symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(report.get('count'), 2)
            self.assertEqual(report.get('min_price'), min_p)
            self.assertEqual(report.get('max_price'), max_p)
            self.assertTrue(report.get(self.symbol))

    def test_generate_symbol_report_dict_data(self):
        price_val = round(random.uniform(100.0, 500.0), 2)
        mock_data = {
            self.symbol: price_val
        }

        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            report = self.generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report.get('count'), 1)
            self.assertEqual(report.get('min_price'), price_val)
            self.assertEqual(report.get('max_price'), price_val)

    def test_generate_symbol_report_no_data(self):
        with patch.object(self.generator.parser, 'load_data', return_value=[]):
            report = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(report.get('count'), 0)
            self.assertIn('error', report)

    def test_generate_symbol_report_no_valid_prices(self):
        mock_data = [
            {"symbol": self.symbol, "price": "".join(random.choices(string.ascii_lowercase, k=6))}
        ]
        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            report = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(report.get('count'), 1)
            self.assertEqual(report.get('error'), 'No valid prices found')

    def test_update_and_fetch_report_with_price(self):
        url = f"https://{uuid.uuid4().hex}.net/api"
        expected_price = round(random.uniform(1.0, 1000.0), 2)

        with patch.object(self.generator.parser, 'fetch_price', return_value=expected_price) as mock_fetch, \
             patch.object(self.generator.parser, 'fetch_and_store') as mock_store:
            
            price = self.generator.update_and_fetch_report(url, self.symbol)
            
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(self.symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_update_and_fetch_report_fallback_price(self):
        url = f"https://{uuid.uuid4().hex}.org/data"

        with patch.object(self.generator.parser, 'fetch_price', return_value=None), \
             patch.object(self.generator.parser, 'fetch_and_store') as mock_store:
            
            price = self.generator.update_and_fetch_report(url, self.symbol)
            
            mock_store.assert_called_once_with(self.symbol, 100.0)
            self.assertEqual(price, 100.0)

    def test_get_raw_stream_dump(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes)
        with patch.object(self.generator.parser, 'load_data', return_value=random_bytes) as mock_load:
            dump = self.generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(dump, random_bytes)

    def test_generate_market_report_function(self):
        price = round(random.uniform(50.0, 150.0), 2)
        mock_data = {
            self.symbol: {"price": price}
        }

        with patch('skills.market_report_generator.db_storage') as mock_db:
            mock_db.load_data.return_value = mock_data
            
            result_str = generate_market_report(self.storage_file, self.symbol)
            
            self.assertIn(self.symbol, result_str)
            self.assertIn(str(price), result_str)

    def test_generate_market_report_fallback_parser(self):
        price = round(random.uniform(1.0, 50.0), 2)
        mock_data = [{
            "symbol": self.symbol,
            "price": price
        }]

        with patch('skills.market_report_generator.db_storage', create=True) as mock_db:
            del mock_db.load_data
            del mock_db.load_db
            
            with patch('skills.market_report_generator.MarketParser') as MockParserClass:
                instance = MockParserClass.return_value
                instance.load_data.return_value = mock_data
                
                result_str = generate_market_report(self.storage_file, self.symbol)
                
                self.assertIn(self.symbol, result_str)
                self.assertIn(str(price), result_str)

if __name__ == '__main__':
    unittest.main()