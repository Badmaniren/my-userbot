import unittest
import os
import json
import uuid
import random
import tempfile
from unittest.mock import patch
from skills.market_portfolio_advanced_metrics import PortfolioAdvancedMetrics


class TestPortfolioAdvancedMetrics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_data(self):
        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        data = metrics_calc.get_metrics_stream_dump()
        self.assertEqual(data, {})

    def test_calculate_advanced_metrics_insufficient_data(self):
        initial_data = {
            self.symbol: [
                {"price": round(random.uniform(10.0, 100.0), 2)}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        result = metrics_calc.calculate_advanced_metrics(self.symbol)

        expected_keys = ["volatility", "sharpe_ratio", "sortino_ratio", "max_drawdown", "risk_metric"]
        for key in expected_keys:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], (int, float))
            self.assertEqual(result[key], 0.0)

    def test_calculate_advanced_metrics_valid_data(self):
        prices = [100.0, 105.0, 102.0, 108.0, 110.0, 107.0, 115.0]
        symbol_data = [{"price": p} for p in prices]
        initial_data = {self.symbol: symbol_data}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        result = metrics_calc.calculate_advanced_metrics(self.symbol, risk_free_rate=0.02)

        self.assertGreaterEqual(result["volatility"], 0.0)
        self.assertGreaterEqual(result["max_drawdown"], 0.0)
        self.assertIsInstance(result["sharpe_ratio"], float)
        self.assertIsInstance(result["sortino_ratio"], float)
        self.assertEqual(result["risk_metric"], result["volatility"])

    def test_evaluate_risk_profile_low(self):
        prices = [100.0, 100.1, 100.2, 100.1, 100.3]
        initial_data = {self.symbol: [{"price": p} for p in prices]}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        profile = metrics_calc.evaluate_risk_profile(self.symbol)

        self.assertIn("risk_level", profile)
        self.assertIn("score", profile)
        self.assertEqual(profile["risk_level"], "LOW")
        self.assertEqual(profile["score"], 1.0)

    def test_evaluate_risk_profile_high(self):
        prices = [10.0, 100.0, 5.0, 200.0, 1.0, 500.0]
        initial_data = {self.symbol: [{"price": p} for p in prices]}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        profile = metrics_calc.evaluate_risk_profile(self.symbol)

        self.assertIn("risk_level", profile)
        self.assertIn("score", profile)
        self.assertEqual(profile["risk_level"], "HIGH")
        self.assertEqual(profile["score"], 9.0)

    def test_get_metrics_stream_dump(self):
        random_price = round(random.uniform(50.0, 500.0), 2)
        initial_data = {
            self.symbol: [
                {"price": random_price}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)
        dump = metrics_calc.get_metrics_stream_dump()

        self.assertIn(self.symbol, dump)
        self.assertEqual(dump[self.symbol][0]["price"], random_price)


if __name__ == "__main__":
    unittest.main()