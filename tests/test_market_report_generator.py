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
        self.generator = MarketReportGenerator(storage_file=self.storage_file)

    def test_generate_symbol_report_with_list_data(self):
        min_p = round(random.uniform(10.0, 50.0), 2)
        max_p = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {"symbol": self.symbol, "price": min_p},
            {"symbol": self.symbol, "price": max_p},
            {"symbol": "".join(random.choices(string.ascii_uppercase, k=4)), "price": 999.9}
        ]

        with patch.object(self.generator.parser, "load_data", return_value=mock_data) as mock_load:
            report = self.generator.generate_symbol_report(self.symbol)
            mock_load.assert_called_once_with(self.storage_file)
            
            self.assertEqual(report.get("count"), 2)
            self.assertEqual(report.get("min_price"), min_p)
            self.assertEqual(report.get("max_price"), max_p)
            self.assertTrue(report.get(self.symbol))

    def test_generate_symbol_report_with_dict_data(self):
        price = round(random.uniform(100.0, 500.0), 2)
        mock_data = {
            self.symbol: price,
            uuid.uuid4().hex: 123.45
        }

        with patch.object(self.generator.parser, "load_data", return_value=mock_data):
            report = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(report.get("count"), 1)
            self.assertEqual(report.get("min_price"), price)
            self.assertEqual(report.get("max_price"), price)

    def test_generate_symbol_report_no_data_found(self):
        with patch.object(self.generator.parser, "load_data", return_value=[]):
            report = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(report.get("count"), 0)
            self.assertEqual(report.get("error"), "No data found")

    def test_generate_symbol_report_no_valid_prices(self):
        mock_data = [
            {"symbol": self.symbol, "price": "invalid_price"},
            {"symbol": self.symbol, "price": {"invalid": "dict"}}
        ]

        with patch.object(self.generator.parser, "load_data", return_value=mock_data):
            report = self.generator.generate_symbol_report(self.symbol)
            self.assertEqual(report.get("count"), 2)
            self.assertEqual(report.get("error"), "No valid prices found")

    def test_update_and_fetch_report_success(self):
        url = f"https://{uuid.uuid4().hex}.com/market"
        expected_price = round(random.uniform(1.0, 1000.0), 2)

        with patch.object(self.generator.parser, "fetch_price", return_value=expected_price) as mock_fetch, \
             patch.object(self.generator.parser, "fetch_and_store") as mock_store:
            
            price = self.generator.update_and_fetch_report(url, self.symbol)
            
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(self.symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_update_and_fetch_report_fallback(self):
        url = f"https://{uuid.uuid4().hex}.org/api"

        with patch.object(self.generator.parser, "fetch_price", return_value=None) as mock_fetch, \
             patch.object(self.generator.parser, "fetch_and_store") as mock_store:
            
            price = self.generator.update_and_fetch_report(url, self.symbol)
            
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(self.symbol, 100.0)
            self.assertEqual(price, 100.0)

    def test_get_raw_stream_dump(self):
        expected_dump = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.generator.parser, "load_data", return_value=expected_dump) as mock_load:
            dump = self.generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(dump, expected_dump)

    def test_generate_market_report_function(self):
        price = round(random.uniform(50.0, 500.0), 2)
        mock_db = MagicMock()
        mock_db.load_data.return_value = {self.symbol: {"price": price}}

        with patch("skills.market_report_generator.db_storage", mock_db):
            result = generate_market_report(self.storage_file, self.symbol)
            mock_db.load_data.assert_called_once_with(self.storage_file)
            self.assertIn(self.symbol, result)
            self.assertIn(str(price), result)


if __name__ == "__main__":
    unittest.main()