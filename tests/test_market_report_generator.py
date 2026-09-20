import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{random.randint(100, 999)}"

    def test_generate_symbol_report_list_data(self):
        min_p = round(random.uniform(1.0, 50.0), 2)
        max_p = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": min_p},
            {"symbol": self.symbol, "price": max_p},
            {"symbol": "INVALID", "price": 999.0}
        ]
        
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report["count"], 2)
            self.assertEqual(report["min_price"], min_p)
            self.assertEqual(report["max_price"], max_p)
            self.assertTrue(report[self.symbol])

    def test_generate_symbol_report_dict_data(self):
        price = round(random.uniform(10.0, 500.0), 2)
        mock_data = {self.symbol: price}
        
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report["count"], 1)
            self.assertEqual(report["min_price"], price)
            self.assertEqual(report["max_price"], price)
            self.assertTrue(report[self.symbol])

    def test_generate_symbol_report_no_data(self):
        with patch("skills.market_parser.MarketParser.load_data", return_value=[]):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report["count"], 0)
            self.assertIn("error", report)

    def test_generate_symbol_report_no_prices(self):
        mock_data = [{"symbol": self.symbol}]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            report = generator.generate_symbol_report(self.symbol)
            
            self.assertEqual(report["count"], 0)
            self.assertIn("error", report)

    def test_update_and_fetch_report(self):
        expected_price = round(random.uniform(1.0, 1000.0), 2)
        
        with patch("skills.market_parser.MarketParser.fetch_price", return_value=expected_price) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            
            generator = MarketReportGenerator(self.storage_file)
            price = generator.update_and_fetch_report(self.url, self.symbol)
            
            mock_fetch.assert_called_once_with(self.url)
            mock_store.assert_called_once_with(self.symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_get_raw_stream_dump(self):
        mock_data = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            generator = MarketReportGenerator(self.storage_file)
            data = generator.get_raw_stream_dump()
            self.assertEqual(data, mock_data)

    def test_generate_market_report_function(self):
        price = round(random.uniform(5.0, 50.0), 2)
        mock_data = {self.symbol: price}
        
        with patch("skills.db_storage.load_data", return_value=mock_data, create=True):
            result = generate_market_report(self.storage_file, self.symbol)
            self.assertIn(self.symbol, result)
            self.assertIn(str(price), result)

    def test_generate_market_report_fallback_load_db(self):
        price = round(random.uniform(50.0, 150.0), 2)
        mock_data = {self.symbol: price}
        
        with patch("skills.db_storage.load_data", side_effect=AttributeError, create=True), \
             patch("skills.db_storage.load_db", return_value=mock_data, create=True):
            
            result = generate_market_report(self.storage_file, self.symbol)
            self.assertIn(self.symbol, result)
            self.assertIn(str(price), result)

if __name__ == "__main__":
    unittest.main()