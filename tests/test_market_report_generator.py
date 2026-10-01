import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGenerator(unittest.TestCase):
    def test_generate_symbol_report_list_data(self):
        sym = uuid.uuid4().hex[:6]
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {"symbol": sym, "price": p1},
            {"symbol": sym, "price": p2}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(uuid.uuid4().hex)
            result = gen.generate_symbol_report(sym)
            self.assertEqual(result.get("count"), 2)
            self.assertEqual(result.get("min_price"), min(p1, p2))
            self.assertEqual(result.get("max_price"), max(p1, p2))

    def test_generate_symbol_report_dict_data(self):
        sym = uuid.uuid4().hex[:6]
        price = round(random.uniform(100.0, 200.0), 2)
        mock_data = {
            sym: {"price": price}
        }
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(uuid.uuid4().hex)
            result = gen.generate_symbol_report(sym)
            self.assertEqual(result.get("count"), 1)
            self.assertEqual(result.get("min_price"), price)
            self.assertEqual(result.get("max_price"), price)

    def test_generate_symbol_report_no_valid_prices(self):
        sym = uuid.uuid4().hex[:6]
        mock_data = [
            {"symbol": sym, "price": uuid.uuid4().hex}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            gen = MarketReportGenerator(uuid.uuid4().hex)
            result = gen.generate_symbol_report(sym)
            self.assertEqual(result.get("count"), 1)
            self.assertEqual(result.get("error"), "No valid prices found")

    def test_update_and_fetch_report(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        sym = uuid.uuid4().hex[:6]
        rand_price = round(random.uniform(1.0, 100.0), 2)
        with patch("skills.market_parser.MarketParser.fetch_price", return_value=rand_price) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            gen = MarketReportGenerator(uuid.uuid4().hex)
            price = gen.update_and_fetch_report(url, sym)
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(sym, rand_price)
            self.assertEqual(price, rand_price)

    def test_update_and_fetch_report_fallback(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        sym = uuid.uuid4().hex[:6]
        with patch("skills.market_parser.MarketParser.fetch_price", return_value=None) as mock_fetch, \
             patch("skills.market_parser.MarketParser.fetch_and_store") as mock_store:
            gen = MarketReportGenerator(uuid.uuid4().hex)
            price = gen.update_and_fetch_report(url, sym)
            mock_fetch.assert_called_once_with(url)
            mock_store.assert_called_once_with(symbol=sym, price=100.0)
            self.assertEqual(price, 100.0)

    def test_get_raw_stream_dump(self):
        dump_data = {uuid.uuid4().hex: random.randint(1, 500)}
        with patch("skills.market_parser.MarketParser.load_data", return_value=dump_data):
            gen = MarketReportGenerator(uuid.uuid4().hex)
            res = gen.get_raw_stream_dump()
            self.assertEqual(res, dump_data)

    def test_generate_market_report_function(self):
        sym = uuid.uuid4().hex[:6]
        price = round(random.uniform(500.0, 1000.0), 2)
        storage = uuid.uuid4().hex
        mock_data = {sym: {"price": price}}
        with patch("skills.db_storage.load_data", return_value=mock_data, create=True):
            report = generate_market_report(storage, sym)
            self.assertIn(sym, report)
            self.assertIn(str(price), report)