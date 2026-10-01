import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):
    
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.generator = MarketReportGenerator(storage_file=self.storage_file)

    def test_generate_symbol_report_list_data(self):
        rand_price_1 = round(random.uniform(10.0, 100.0), 2)
        rand_price_2 = round(random.uniform(101.0, 200.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": rand_price_1},
            {"symbol": self.symbol, "price": {"price": rand_price_2}},
            {"symbol": "INVALID", "price": 999.0}
        ]
        
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data) as mock_load:
            result = self.generator.generate_symbol_report(self.symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            self.assertTrue(result.get(self.symbol))
            self.assertEqual(result.get("count"), 2)
            self.assertEqual(result.get("min_price"), min(rand_price_1, rand_price_2))
            self.assertEqual(result.get("max_price"), max(rand_price_1, rand_price_2))

    def test_generate_symbol_report_dict_data(self):
        rand_price = round(random.uniform(500.0, 1000.0), 2)
        mock_data = {
            self.symbol: rand_price
        }
        
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data) as mock_load:
            result = self.generator.generate_symbol_report(self.symbol)
            
            mock_load.assert_called_once_with(self.storage_file)
            self.assertTrue(result.get(self.symbol))
            self.assertEqual(result.get("count"), 1)
            self.assertEqual(result.get("min_price"), rand_price)
            self.assertEqual(result.get("max_price"), rand_price)

    def test_generate_symbol_report_no_data(self):
        with patch("skills.market_parser.MarketParser.load_data", return_value=[]):
            result = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(result.get("count"), 0)
            self.assertIn("error", result)

    def test_generate_symbol_report_no_valid_prices(self):
        mock_data = [
            {"symbol": self.symbol, "price": "not_a_number"}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            result = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(result.get("count"), 1)
            self.assertEqual(result.get("error"), "No valid prices found")

    def test_update_and_fetch_report_success(self):
        rand_url = f"https://{uuid.uuid4().hex}.com/api"
        rand_price = round(random.uniform(1.0, 50.0), 2)
        
        with patch("skills.market_parser.MarketParser.fetch_price", return_value=rand_price) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            
            price = self.generator.update_and_fetch_report(rand_url, self.symbol)
            
            mock_fetch.assert_called_once_with(rand_url)
            mock_store.assert_called_once_with(self.symbol, rand_price)
            self.assertEqual(price, rand_price)

    def test_update_and_fetch_report_fallback(self):
        rand_url = f"https://{uuid.uuid4().hex}.org/stream"
        
        with patch("skills.market_parser.MarketParser.fetch_price", return_value=None) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            
            price = self.generator.update_and_fetch_report(rand_url, self.symbol)
            
            mock_fetch.assert_called_once_with(rand_url)
            mock_store.assert_called_once_with(self.symbol, 100.0)
            self.assertEqual(price, 100.0)

    def test_get_raw_stream_dump(self):
        rand_dump = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch("skills.market_parser.MarketParser.load_data", return_value=rand_dump) as mock_load:
            dump = self.generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(dump, rand_dump)

    def test_generate_market_report_with_db_load(self):
        rand_price = round(random.uniform(1000.0, 5000.0), 2)
        mock_data = {
            self.symbol: {"price": rand_price}
        }
        
        with patch("skills.market_report_generator.db_storage") as mock_db:
            mock_db.load_data.return_value = mock_data
            
            report = generate_market_report(self.storage_file, self.symbol)
            
            mock_db.load_data.assert_called_once_with(self.storage_file)
            self.assertIn(self.symbol, report)
            self.assertIn(str(rand_price), report)

    def test_generate_market_report_fallback_to_parser(self):
        rand_price = round(random.uniform(50.0, 100.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": rand_price}
        ]
        
        with patch("skills.market_report_generator.db_storage") as mock_db, \
             patch("skills.market_parser.MarketParser.load_data", return_value=mock_data) as mock_parser_load:
            
            mock_db.load_data.side_effect = AttributeError("No load_data")
            mock_db.load_db.side_effect = AttributeError("No load_db")
            
            report = generate_market_report(self.storage_file, self.symbol)
            
            mock_parser_load.assert_called_once_with(self.storage_file)
            self.assertIn(self.symbol, report)
            self.assertIn(str(rand_price), report)

if __name__ == "__main__":
    unittest.main()