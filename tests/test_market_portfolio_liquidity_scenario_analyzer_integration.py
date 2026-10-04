import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_liquidity_scenario_analyzer import (
    analyze_liquidity_stress_scenarios,
    MarketPortfolioLiquidityScenarioAnalyzer
)

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(10, 99)}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.percentage = round(random.uniform(0.01, 0.20), 4)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        
        self.export_target = f"test_output_{uuid.uuid4().hex[:6]}.json"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:6]}.json"

    def tearDown(self):
        for file_path in [self.export_target, self.storage_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_analyze_liquidity_stress_scenarios_integration(self):
        result = analyze_liquidity_stress_scenarios(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_liquidity_data", result)
        self.assertIn("stress_pipeline_data", result)
        self.assertIn("reserve_capital_requirement", result)
        self.assertIsInstance(result["reserve_capital_requirement"], float)

        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.export_target, 'r') as f:
            export_content = json.load(f)
            self.assertIsInstance(export_content, dict)

        with open(self.storage_file, 'r') as f:
            storage_content = json.load(f)
            self.assertIsInstance(storage_content, dict)

    def test_market_portfolio_liquidity_scenario_analyzer_class_integration(self):
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
        
        evaluation_result = analyzer.evaluate_portfolio(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(evaluation_result, dict)
        self.assertEqual(evaluation_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_result", evaluation_result)
        self.assertIn("stress_result", evaluation_result)

        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()