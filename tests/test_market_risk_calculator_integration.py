import unittest
import os
import json
import uuid
import random
from skills.market_risk_calculator import (
    MarketRiskCalculator,
    calculate_market_risks,
    calculate_volatility,
    calculate_max_drawdown
)
from skills.market_parser import MarketParser


class TestMarketRiskCalculatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex[:8]
        self.storage_file = os.path.join(self.test_dir, f"market_storage_{unique_id}.json")

        self.symbol = f"TICKER_{random.randint(1000, 9999)}"

        self.parser = MarketParser(self.storage_file)
        self.calculator = MarketRiskCalculator(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_integration_risk_calculation_pipeline(self):
        random_prices = [round(random.uniform(100.0, 500.0), 2) for _ in range(5)]

        for price in random_prices:
            self.parser.fetch_and_store(self.symbol, price)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища не был создан через MarketParser")

        evaluated_risk = self.calculator.evaluate_risk(self.symbol)

        self.assertIn("symbol", evaluated_risk)
        self.assertIn("volatility", evaluated_risk)
        self.assertIn("max_drawdown", evaluated_risk)
        self.assertEqual(evaluated_risk["symbol"], self.symbol)

        summary_risk = self.calculator.get_risk_summary(self.symbol)

        self.assertIn("cost_dynamics", summary_risk)
        self.assertEqual(summary_risk["cost_dynamics"], random_prices)

        standalone_risk = calculate_market_risks(self.storage_file, self.symbol)

        self.assertEqual(standalone_risk["symbol"], self.symbol)
        self.assertEqual(standalone_risk["cost_dynamics"], random_prices)
        self.assertEqual(standalone_risk["volatility"], evaluated_risk["volatility"])
        self.assertEqual(standalone_risk["max_drawdown"], evaluated_risk["max_drawdown"])

    def test_integration_empty_storage(self):
        empty_risk = self.calculator.evaluate_risk(self.symbol)

        self.assertEqual(empty_risk["symbol"], self.symbol)
        self.assertEqual(empty_risk["volatility"], 0.0)
        self.assertEqual(empty_risk["max_drawdown"], 0.0)

        summary = self.calculator.get_risk_summary(self.symbol)
        self.assertEqual(summary["cost_dynamics"], [])


if __name__ == "__main__":
    unittest.main()