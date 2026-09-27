import unittest
import uuid
import os
import tempfile
from skills.market_portfolio_rebalance_calculator import PortfolioRebalanceCalculator

class TestPortfolioRebalanceCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            f.write('{"initial": "data"}')

        self.calculator = PortfolioRebalanceCalculator(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_calculate_rebalance_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = float(uuid.uuid4().int % 100) / 10.0
        percentage = float(uuid.uuid4().int % 1000) / 10.0

        result = self.calculator.calculate_rebalance(symbol, shifts, percentage)

        self.assertIn("target_weights", result)
        self.assertIn("deviations", result)
        self.assertIn("metrics", result)
        self.assertIn("strategy", result)

        self.assertEqual(result["target_weights"][symbol], percentage)
        self.assertEqual(result["deviations"][symbol], shifts)
        self.assertIsInstance(result["metrics"], dict)
        self.assertIsInstance(result["strategy"], dict)

    def test_evaluate_rebalance_strategy_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = float(uuid.uuid4().int % 100) / 10.0

        result = self.calculator.evaluate_rebalance_strategy(symbol, shifts)

        self.assertIn("symbol", result)
        self.assertIn("performance_evaluation", result)
        self.assertIn("resilience_evaluation", result)
        self.assertEqual(result["symbol"], symbol)
        self.assertIsInstance(result["performance_evaluation"], dict)
        self.assertIsInstance(result["resilience_evaluation"], dict)

    def test_analyze_stream_and_summary_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        stream_file = os.path.join(self.test_dir.name, f"stream_{uuid.uuid4()}.json")

        stream_content = f'{{"stream_id": "{uuid.uuid4()}"}}'
        with open(stream_file, 'w', encoding='utf-8') as f:
            f.write(stream_content)

        result = self.calculator.analyze_stream_and_summary(stream_file, symbol)

        self.assertIn("stream_data", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], dict)

    def test_full_rebalance_cycle_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        allocation = float(uuid.uuid4().int % 1000) / 10.0
        shifts = float(uuid.uuid4().int % 100) / 10.0

        result = self.calculator.full_rebalance_cycle(symbol, allocation, shifts)

        self.assertIsInstance(result, dict)

if __name__ == "__main__":
    unittest.main()