import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import os

from skills.market_portfolio_performance_analytics import start_new

class TestMarketPortfolioPerformanceAnalytics(unittest.TestCase):

    def test_start_new_returns_expected_analytics_structure(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_storage = f"{uuid.uuid4().hex}.json"
        random_url = f"https://{uuid.uuid4().hex}.com/market"
        
        mock_prices = [
            {"symbol": random_symbol, "price": round(random.uniform(10.0, 1000.0), 2)} 
            for _ in range(10)
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_prices
            instance.fetch_price.return_value = round(random.uniform(10.0, 1000.0), 2)

            result = start_new(random_storage, random_symbol, random_url)

            self.assertIsInstance(result, dict)
            self.assertIn("symbol", result)
            self.assertIn("return", result)
            self.assertIn("volatility", result)
            self.assertIn("sharpe_ratio", result)
            self.assertEqual(result["symbol"], random_symbol)

    def test_start_new_calculates_correct_metrics_with_chaos_data(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        random_storage = f"storage_{uuid.uuid4().hex}"
        random_url = f"http://{uuid.uuid4().hex}.local/api"

        base_price = random.uniform(50.0, 500.0)
        price_fluctuations = [base_price * (1 + random.uniform(-0.1, 0.1)) for _ in range(15)]
        
        mock_data = [{"symbol": random_symbol, "price": p} for p in price_fluctuations]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analysis_result = start_new(storage_file=random_storage, symbol=random_symbol, url=random_url)

            self.assertIsInstance(analysis_result.get("return"), float)
            self.assertIsInstance(analysis_result.get("volatility"), float)
            self.assertIsInstance(analysis_result.get("sharpe_ratio"), float)
            
            instance.load_data.assert_called_once_with(random_storage)

    def test_start_new_handles_empty_dataset_gracefully(self):
        random_symbol = uuid.uuid4().hex[:6].upper()
        random_storage = f"{uuid.uuid4().hex}.db"
        random_url = f"https://{uuid.uuid4().hex}.org/feed"

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = []

            result = start_new(random_storage, random_symbol, random_url)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("return"), 0.0)
            self.assertEqual(result.get("volatility"), 0.0)
            self.assertEqual(result.get("sharpe_ratio"), 0.0)
            self.assertEqual(result.get("symbol"), random_symbol)

    def test_start_new_integration_with_io_stream(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_storage = f"{uuid.uuid4().hex}.dat"
        random_url = f"https://{uuid.uuid4().hex}.net/stream"
        
        raw_payload = json.dumps([
            {"symbol": random_symbol, "price": 100.0},
            {"symbol": random_symbol, "price": 105.0},
            {"symbol": random_symbol, "price": 102.0}
        ]).encode('utf-8')

        mock_file_stream = io.BytesIO(raw_payload)

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = json.loads(mock_file_stream.read().decode('utf-8'))

            res = start_new(random_storage, random_symbol, random_url)
            
            self.assertIsNotNone(res)
            self.assertIn("sharpe_ratio", res)
            self.assertGreaterEqual(res["volatility"], 0.0)