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
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api/v1/price"

    def test_market_report_generator_init(self):
        generator = MarketReportGenerator(self.storage_file)
        self.assertEqual(generator.storage_file, self.storage_file)
        self.assertIsNotNone(generator.parser)

    def test_generate_symbol_report_list_data(self):
        random_price_1 = round(random.uniform(10.0, 100.0), 2)
        random_price_2 = round(random.uniform(101.0, 200.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": random_price_1},
            {"symbol": self.symbol, "price": random_price_2},
            {"symbol": "OTHER", "price": 999.0}
        ]
        
        with patch('skills.market_parser.MarketParser.load_data', return_value=mock_data) as mock_load:
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            self.assertTrue(report.get(self.symbol))
            self.assertEqual(report.get('count'), 2)
            self.assertEqual(report.get('min_price'), min(random_price_1, random_price_2))
            self.assertEqual(report.get('max_price'), max(random_price_1, random_price_2))

    def test_generate_symbol_report_dict_data(self):
        random_price = round(random.uniform(50.0, 500.0), 2)
        mock_data = {
            self.symbol: random_price,
            f"OTHER_{uuid.uuid4().hex[:4]}": 123.45
        }
        
        with patch('skills.market_parser.MarketParser.load_data', return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertTrue(report.get(self.symbol))
            self.assertEqual(report.get('count'), 1)
            self.assertEqual(report.get('min_price'), random_price)
            self.assertEqual(report.get('max_price'), random_price)

    def test_generate_symbol_report_no_data(self):
        with patch('skills.market_parser.MarketParser.load_data', return_value=[]):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report.get('count'), 0)
            self.assertIn('error', report)

    def test_generate_symbol_report_no_valid_prices(self):
        mock_data = [{"symbol": self.symbol, "price": f"invalid_{uuid.uuid4().hex[:4]}"}]
        with patch('skills.market_parser.MarketParser.load_data', return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report.get('count'), 1)
            self.assertEqual(report.get('error'), "No valid prices found")

    def test_update_and_fetch_report_success(self):
        expected_price = round(random.uniform(1.0, 1000.0), 2)
        with patch('skills.market_parser.MarketParser.fetch_price', return_value=expected_price) as mock_fetch, \
             patch('skills.market_parser.MarketParser.fetch_and_store') as mock_store:
            
            generator = MarketReportGenerator(self.storage_file)
            price = generator.update_and_fetch_report(self.url, self.symbol)
            
            mock_fetch.assert_called_once_with(self.url)
            mock_store.assert_called_once_with(self.symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_update_and_fetch_report_fallback(self):
        with patch('skills.market_parser.MarketParser.fetch_price', return_value=None) as mock_fetch, \
             patch('skills.market_parser.MarketParser.fetch_and_store') as mock_store:
            
            generator = MarketReportGenerator(self.storage_file)
            price = generator.update_and_fetch_report(self.url, self.symbol)
            
            mock_fetch.assert_called_once_with(self.url)
            mock_store.assert_called_once_with(self.symbol, 100.0)
            self.assertEqual(price, 100.0)

    def test_get_raw_stream_dump(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch('skills.market_parser.MarketParser.load_data', return_value=stream_data) as mock_load:
            generator = MarketReportGenerator(self.storage_file)
            res = generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(res, stream_data)

    def test_generate_market_report_success_db(self):
        expected_price = round(random.uniform(10.0, 500.0), 2)
        mock_db = MagicMock()
        mock_db.load_data.return_value = {self.symbol: {"price": expected_price}}
        
        with patch('skills.market_report_generator.db_storage', mock_db):
            result = generate_market_report(self.storage_file, self.symbol)
            mock_db.load_data.assert_called_once_with(self.storage_file)
            self.assertIn(f"Report for {self.symbol}: price {expected_price}", result)

    def test_generate_market_report_fallback_to_load_db(self):
        expected_price = round(random.uniform(10.0, 500.0), 2)
        mock_db = MagicMock()
        del mock_db.load_data
        mock_db.load_db.return_value = {self.symbol: expected_price}
        
        with patch('skills.market_report_generator.db_storage', mock_db):
            result = generate_market_report(self.storage_file, self.symbol)
            mock_db.load_db.assert_called_once_with(self.storage_file)
            self.assertIn(f"Report for {self.symbol}: price {expected_price}", result)

    def test_generate_market_report_fallback_to_parser(self):
        mock_db = MagicMock()
        if hasattr(mock_db, 'load_data'):
            del mock_db.load_data
        if hasattr(mock_db, 'load_db'):
            del mock_db.load_db
            
        expected_price = round(random.uniform(10.0, 500.0), 2)
        
        with patch('skills.market_report_generator.db_storage', mock_db), \
             patch('skills.market_parser.MarketParser.load_data', return_value=[{"symbol": self.symbol, "price": expected_price}]) as mock_parser_load:
            
            result = generate_market_report(self.storage_file, self.symbol)
            mock_parser_load.assert_called_with(self.storage_file)
            self.assertIn(f"Report for {self.symbol}: price {expected_price}", result)