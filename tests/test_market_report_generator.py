import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):

    def test_generate_symbol_report_valid_list(self):
        sym = uuid.uuid4().hex[:6]
        p1 = random.uniform(10.0, 50.0)
        p2 = random.uniform(51.0, 100.0)
        mock_data = [
            {"symbol": sym, "price": p1},
            {"symbol": sym, "price": p2},
            {"symbol": uuid.uuid4().hex[:6], "price": 999.0}
        ]

        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            res = gen.generate_symbol_report(sym)
            
            self.assertEqual(res.get("count"), 2)
            self.assertEqual(res.get("min_price"), min(p1, p2))
            self.assertEqual(res.get("max_price"), max(p1, p2))
            self.assertTrue(res.get(sym))

    def test_generate_symbol_report_valid_dict(self):
        sym = uuid.uuid4().hex[:6]
        price = random.uniform(100.0, 200.0)
        mock_data = {sym: price}

        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            res = gen.generate_symbol_report(sym)

            self.assertEqual(res.get("count"), 1)
            self.assertEqual(res.get("min_price"), price)
            self.assertEqual(res.get("max_price"), price)
            self.assertTrue(res.get(sym))

    def test_generate_symbol_report_no_data(self):
        sym = uuid.uuid4().hex[:6]
        with patch("skills.market_parser.MarketParser.load_data", return_value=[]):
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            res = gen.generate_symbol_report(sym)

            self.assertEqual(res.get("count"), 0)
            self.assertIn("error", res)

    def test_generate_symbol_report_no_valid_prices(self):
        sym = uuid.uuid4().hex[:6]
        mock_data = [{"symbol": sym, "price": "invalid_price"}]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            res = gen.generate_symbol_report(sym)

            self.assertEqual(res.get("count"), 1)
            self.assertIn("error", res)

    def test_update_and_fetch_report_success(self):
        url = f"https://{uuid.uuid4().hex}.com/market"
        sym = uuid.uuid4().hex[:6]
        expected_price = round(random.uniform(1.0, 1000.0), 2)

        with patch("skills.market_parser.MarketParser.fetch_price", return_value=expected_price) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            val = gen.update_and_fetch_report(url, sym)
            
            self.assertEqual(val, float(expected_price))
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(sym, expected_price)

    def test_update_and_fetch_report_fallback(self):
        url = f"https://{uuid.uuid4().hex}.com/market"
        sym = uuid.uuid4().hex[:6]

        with patch("skills.market_parser.MarketParser.fetch_price", return_value=None) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            gen = MarketReportGenerator(storage_file=uuid.uuid4().hex)
            val = gen.update_and_fetch_report(url, sym)
            
            self.assertEqual(val, 100.0)
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(sym, 100.0)

    def test_get_raw_stream_dump(self):
        expected_dump = {uuid.uuid4().hex: random.randint(1, 100)}
        storage = uuid.uuid4().hex
        with patch("skills.market_parser.MarketParser.load_data", return_value=expected_dump) as mock_load:
            gen = MarketReportGenerator(storage_file=storage)
            dump = gen.get_raw_stream_dump()

            self.assertEqual(dump, expected_dump)
            mock_load.assert_called_once_with(storage)

    def test_generate_market_report_db_load_dict(self):
        sym = uuid.uuid4().hex[:6]
        price = round(random.uniform(10.0, 500.0), 2)
        storage = uuid.uuid4().hex
        mock_data = {sym: {"price": price}}

        with patch("skills.db_storage.load_db", return_value=mock_data):
            report = generate_market_report(storage, sym)
            self.assertIn(sym, report)
            self.assertIn(str(price), report)

    def test_generate_market_report_db_load_list(self):
        sym = uuid.uuid4().hex[:6]
        price = round(random.uniform(10.0, 500.0), 2)
        storage = uuid.uuid4().hex
        mock_data = [{"symbol": sym, "price": price}]

        with patch("skills.db_storage.load_db", return_value=mock_data):
            report = generate_market_report(storage, sym)
            self.assertIn(sym, report)
            self.assertIn(str(price), report)

    def test_generate_market_report_fallback_parser(self):
        sym = uuid.uuid4().hex[:6]
        price = round(random.uniform(10.0, 500.0), 2)
        storage = uuid.uuid4().hex
        mock_data = {sym: price}

        with patch("skills.db_storage.load_db", return_value={}), \
             patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            report = generate_market_report(storage, sym)
            self.assertIn(sym, report)
            self.assertIn(str(price), report)