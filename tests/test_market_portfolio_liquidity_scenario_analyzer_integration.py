import unittest
import os
import uuid
import tempfile
import json
from skills.market_portfolio_liquidity_scenario_analyzer import (
    analyze_liquidity_stress_scenarios,
    MarketPortfolioLiquidityScenarioAnalyzer
)

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.symbol = f"SYM-{uuid.uuid4().hex[:6].upper()}"
        self.confidence_level = round(0.90 + (uuid.uuid4().int % 9) / 100.0, 2)
        self.percentage = float(uuid.uuid4().int % 15 + 1)
        self.shifts = [float(uuid.uuid4().int % 5 - 2), float(uuid.uuid4().int % 10 + 1)]
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_target = os.path.join(self.temp_dir.name, f"export_{uuid.uuid4().hex}.json")
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

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
        self.assertGreaterEqual(result["reserve_capital_requirement"], 0.0)

        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.export_target, 'r') as f:
            exported_data = json.load(f)
            self.assertIsInstance(exported_data, dict)

        with open(self.storage_file, 'r') as f:
            stored_data = json.load(f)
            self.assertIsInstance(stored_data, dict)

    def test_market_portfolio_liquidity_scenario_analyzer_class_integration(self):
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
        
        eval_result = analyzer.evaluate_portfolio(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(eval_result, dict)
        self.assertEqual(eval_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_result", eval_result)
        self.assertIn("stress_result", eval_result)

        calculated_reserve = analyzer._calculate_required_reserve(100.0, 200.0)
        self.assertEqual(calculated_reserve, 230.0)

if __name__ == "__main__":
    unittest.main()