import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:4]}"
        self.generator = MarketReportGenerator(storage_file=self.random_storage)

    def test_generate_symbol_report_with_list_data(self):
        min_p = round(random.uniform(1.0, 50.0), 2)
        max_p = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {"symbol": self.random_symbol, "price": min_p},
            {"symbol": self.random_symbol, "price": max_p},
            {"symbol": f"OTHER_{uuid.uuid4().hex[:4]}", "price": 999.0}
        ]
        
        with patch.object(self.generator.parser, 'load_data', return_value=mock_data) as mock_load:
            report = self.generator.generate_symbol_report(self.random_symbol)
            mock_load.assert_called_once_with(self.random_storage)
            self.assertEqual(report.get("count"), 2)
            self.assertEqual(report.get("min_price"), min_p)
            self.assertEqual(report.get("max_price"), max_p)
            self.assertTrue(report.get(self.random_symbol))

    def test_generate_symbol_report_with_dict_data(self):
        expected_price = round(random.uniform(10.0, 500.0), 2)
        mock_data = {
            self.random_symbol: expected_price
        }

        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            report = self.generator.generate_symbol_report(self.random_symbol)
            self.assertEqual(report.get("count"), 1)
            self.assertEqual(report.get("min_price"), expected_price)
            self.assertEqual(report.get("max_price"), expected_price)

    def test_generate_symbol_report_no_data(self):
        with patch.object(self.generator.parser, 'load_data', return_value=[]):
            report = self.generator.generate_symbol_report(self.random_symbol)
            self.assertEqual(report.get("count"), 0)
            self.assertIn("error", report)

    def test_generate_symbol_report_no_valid_prices(self):
        mock_data = [
            {"symbol": self.random_symbol, "price": f"INVALID_{uuid.uuid4().hex[:4]}"}
        ]
        with patch.object(self.generator.parser, 'load_data', return_value=mock_data):
            report = self.generator.generate_symbol_report(self.random_symbol)
            self.assertEqual(report.get("count"), 1)
            self.assertIn("error", report)

    def test_update_and_fetch_report(self):
        expected_price = round(random.uniform(100.0, 1000.0), 2)
        with patch.object(self.generator.parser, 'fetch_price', return_value=expected_price) as mock_fetch, \
             patch.object(self.generator.parser, 'fetch_and_store') as mock_store:
            
            price = self.generator.update_and_fetch_report(self.random_url, self.random_symbol)
            mock_fetch.assert_called_once_with(self.random_url)
            mock_store.assert_called_once_with(self.random_symbol, expected_price)
            self.assertEqual(price, expected_price)

    def test_get_raw_stream_dump(self):
        random_dump = {uuid.uuid4().hex: random.randint(1, 100)}
        with patch.object(self.generator.parser, 'load_data', return_value=random_dump) as mock_load:
            dump = self.generator.get_raw_stream_dump()
            mock_load.assert_called_once_with(self.random_storage)
            self.assertEqual(dump, random_dump)

    def test_generate_market_report_function(self):
        expected_price = round(random.uniform(5.0, 50.0), 2)
        mock_db = MagicMock()
        mock_db.load_data.return_value = {self.random_symbol: {"price": expected_price}}

        with patch("skills.market_report_generator.db_storage", mock_db):
            result_str = generate_market_report(self.random_storage, self.random_symbol)
            self.assertIn(self.random_symbol, result_str)
            self.assertIn(str(expected_price), result_str)

    def test_generate_market_report_with_fallback(self):
        expected_price = round(random.uniform(10.0, 20.0), 2)
        mock_db = MagicMock()
        del mock_db.load_data
        mock_db.load_db.return_value = {self.random_symbol: expected_price}

        with patch("skills.market_report_generator.db_storage", mock_db):
            result_str = generate_market_report(self.random_storage, self.random_symbol)
            self.assertIn(self.random_symbol, result_str)
            self.assertIn(str(expected_price), result_str)

    def test_stream_bytes_io_mocking(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        self.assertEqual(stream.read(), random_bytes)

if __name__ == '__main__':
    unittest.main()