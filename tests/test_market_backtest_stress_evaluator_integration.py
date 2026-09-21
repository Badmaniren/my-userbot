import unittest
import os
import tempfile
import uuid
import random
from skills.market_backtest_stress_evaluator import MarketBacktestStressEvaluator


class TestMarketBacktestStressEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")

        # Создаем минимальный файл хранилища с тестовыми данными, чтобы зависимые навыки не падали при чтении
        import json
        initial_data = {
            "BTC": [
                {"price": 100.0, "timestamp": "2023-01-01"},
                {"price": 105.0, "timestamp": "2023-01-02"},
                {"price": 110.0, "timestamp": "2023-01-03"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        self.evaluator = MarketBacktestStressEvaluator(storage_file=self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_evaluate_strategy_stress_and_backtest_integration(self):
        symbol = f"COIN_{uuid.uuid4().hex[:6]}"
        shifts = [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)]
        strategy_params = {"initial_capital": random.randint(1000, 10000), "risk_tolerance": random.random()}

        result = self.evaluator.evaluate_strategy_stress_and_backtest(symbol, shifts, strategy_params)

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("stress_test_results", result)

    def test_run_comprehensive_evaluation_stream_integration(self):
        symbol = f"TOKEN_{uuid.uuid4().hex[:6]}"
        shifts = [random.uniform(-0.2, 0.2)]
        params = {"capital": random.randint(5000, 20000)}
        percentage = random.uniform(1.0, 15.0)

        result = self.evaluator.run_comprehensive_evaluation_stream(symbol, shifts, params, percentage)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), symbol)
        self.assertIn("backtest", result)
        self.assertIn("scenario_simulation", result)

    def test_evaluate_strategy_stress_integration(self):
        symbol = f"ASSET_{uuid.uuid4().hex[:6]}"
        initial_capital = float(random.randint(1000, 50000))
        shift = random.uniform(-0.05, 0.05)

        result = self.evaluator.evaluate_strategy_stress(symbol, initial_capital, shift)

        self.assertIsInstance(result, dict)
        self.assertIn("backtest", result)
        self.assertIn("stress_test", result)


if __name__ == "__main__":
    unittest.main()