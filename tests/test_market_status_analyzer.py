import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_status_analyzer import MarketStatusAnalyzer

class TestMarketStatusAnalyzer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"db_{uuid.uuid4().hex}.sqlite"
        self.analyzer = MarketStatusAnalyzer(self.storage_file)

    def test_compute_base_metrics_empty(self):
        prices = []
        metrics = self.analyzer.compute_base_metrics(prices)
        self.assertEqual(metrics["min"], 0.0)
        self.assertEqual(metrics["max"], 0.0)
        self.assertEqual(metrics["average"], 0.0)

    def test_compute_base_metrics_success(self):
        p1 = random.uniform(10.0, 50.0)
        p2 = random.uniform(51.0, 100.0)
        p3 = random.uniform(101.0, 150.0)
        prices = [p1, p2, p3]
        metrics = self.analyzer.compute_base_metrics(prices)
        self.assertEqual(metrics["min"], min(prices))
        self.assertEqual(metrics["max"], max(prices))
        self.assertEqual(metrics["average"], sum(prices) / 3)

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_analyze_market_status_bullish(self, mock_fetch_price):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        url = f"https://{uuid.uuid4().hex}.com/market"
        current_p = random.uniform(200.0, 300.0)
        mock_fetch_price.return_value = current_p

        p_old = current_p - random.uniform(10.0, 50.0)
        p_new = current_p

        mock_storage = MagicMock()
        mock_storage.load_data.return_value = [
            {"symbol": symbol, "price": p_old},
            {"symbol": symbol, "price": p_new}
        ]
        self.analyzer.storage = mock_storage

        result = self.analyzer.analyze_market_status(symbol, url=url)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["current_price"], current_p)
        self.assertEqual(result["trend"], "bullish")
        self.assertIn("min", result)
        self.assertIn("max", result)
        self.assertIn("average", result)

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_analyze_market_status_bearish(self, mock_fetch_price):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        url = f"https://{uuid.uuid4().hex}.org/api"
        current_p = random.uniform(50.0, 100.0)
        mock_fetch_price.return_value = current_p

        p_old = current_p + random.uniform(10.0, 50.0)
        p_new = current_p

        mock_storage = MagicMock()
        mock_storage.load_data.return_value = [
            {"symbol": symbol, "price": p_old},
            {"symbol": symbol, "price": p_new}
        ]
        self.analyzer.storage = mock_storage

        result = self.analyzer.analyze_market_status(url, symbol)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["current_price"], current_p)
        self.assertEqual(result["trend"], "bearish")

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_analyze_market_status_neutral(self, mock_fetch_price):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        current_p = 100.0
        mock_fetch_price.return_value = current_p

        mock_storage = MagicMock()
        mock_storage.load_data.return_value = [
            {"symbol": symbol, "price": 100.0}
        ]
        self.analyzer.storage = mock_storage

        result = self.analyzer.analyze_market_status(symbol=symbol)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["trend"], "neutral")

    def test_fetch_and_evaluate_stream(self):
        url = f"https://{uuid.uuid4().hex}.net/stream"
        expected_prices = [random.uniform(1.0, 10.0), random.uniform(11.0, 20.0)]

        with patch('skills.market_parser.MarketParser.parse_html_prices', return_value=expected_prices) as mock_parse:
            res = self.analyzer.fetch_and_evaluate_stream(url)
            mock_parse.assert_called_once_with(url)
            self.assertEqual(res, expected_prices)

if __name__ == '__main__':
    unittest.main()