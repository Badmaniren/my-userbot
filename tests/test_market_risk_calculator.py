import unittest
from unittest.mock import patch
import json
import uuid
import random
import statistics
from skills.market_risk_calculator import (
    calculate_volatility,
    calculate_max_drawdown,
    MarketRiskCalculator,
    calculate_market_risks
)


class TestMarketRiskCalculator(unittest.TestCase):

    def test_calculate_volatility_edge_cases(self):
        self.assertEqual(calculate_volatility([]), 0.0)
        self.assertEqual(calculate_volatility([random.uniform(1.0, 100.0)]), 0.0)

    def test_calculate_volatility_valid(self):
        rand_base = random.uniform(10.0, 50.0)
        prices = [rand_base, rand_base + random.uniform(1.0, 5.0), rand_base + random.uniform(6.0, 10.0)]
        expected = float(statistics.stdev(prices))
        self.assertAlmostEqual(calculate_volatility(prices), expected)

    def test_calculate_max_drawdown_edge_cases(self):
        self.assertEqual(calculate_max_drawdown([]), 0.0)
        self.assertEqual(calculate_max_drawdown([random.uniform(1.0, 100.0)]), 0.0)

    def test_calculate_max_drawdown_valid(self):
        peak = random.uniform(100.0, 200.0)
        trough = peak * random.uniform(0.5, 0.8)
        prices = [peak, trough, peak * 1.1]
        expected = (trough - peak) / peak
        self.assertAlmostEqual(calculate_max_drawdown(prices), float(expected))

    def test_market_risk_calculator_load_data_file_not_found(self):
        fake_file = f"{uuid.uuid4().hex}.json"
        calc = MarketRiskCalculator(fake_file)
        self.assertEqual(calc.load_data(fake_file), [])

    def test_market_risk_calculator_load_data_success(self):
        fake_file = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:6]
        rand_price = random.uniform(10.0, 1000.0)
        mock_data = [{"symbol": rand_symbol, "price": rand_price}]

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            calc = MarketRiskCalculator(fake_file)
            data = calc.load_data(fake_file)
            self.assertEqual(data, mock_data)

    def test_market_risk_calculator_evaluate_and_summary(self):
        fake_file = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:8]
        p1 = random.uniform(50.0, 100.0)
        p2 = p1 * 1.2
        p3 = p1 * 0.9

        mock_data = [
            {"symbol": rand_symbol, "price": p1},
            {"ticker": rand_symbol, "price": p2},
            {"symbol": rand_symbol, "price": p3},
            {"symbol": uuid.uuid4().hex[:8], "price": 999.9}
        ]

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            calc = MarketRiskCalculator(fake_file)

            eval_res = calc.evaluate_risk(rand_symbol)
            self.assertEqual(eval_res["symbol"], rand_symbol)
            self.assertIn("volatility", eval_res)
            self.assertIn("max_drawdown", eval_res)
            self.assertNotIn("cost_dynamics", eval_res)

            summary_res = calc.get_risk_summary(rand_symbol)
            self.assertEqual(summary_res["symbol"], rand_symbol)
            self.assertEqual(summary_res["cost_dynamics"], [p1, p2, p3])

    def test_calculate_market_risks_function(self):
        fake_file = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:8]
        prices = [random.uniform(10.0, 50.0) for _ in range(5)]
        mock_data = [{"symbol": rand_symbol, "price": p} for p in prices]

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            res = calculate_market_risks(fake_file, rand_symbol)
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertEqual(res["cost_dynamics"], prices)
            self.assertIsInstance(res["volatility"], float)
            self.assertIsInstance(res["max_drawdown"], float)


if __name__ == "__main__":
    unittest.main()