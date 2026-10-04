import unittest
import os
import tempfile
import uuid
import json
from skills import market_portfolio_liquidity_scenario_analyzer

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        self.confidence_level = round(float(uuid.uuid4().int % 100) / 100.0 + 0.5, 2)
        if self.confidence_level >= 1.0:
            self.confidence_level = 0.95
        self.percentage = float(uuid.uuid4().int % 20 + 1)
        self.shifts = [float(uuid.uuid4().int % 10), float(uuid.uuid4().int % 15)]
        
        self.export_target = os.path.join(self.test_dir.name, f"export_{uuid.uuid4().hex[:6]}.json")
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex[:6]}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_analyze_liquidity_stress_scenarios_integration(self):
        result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
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

        self.assertTrue(os.path.exists(self.export_target), "Export target file must be created")
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created")

        with open(self.export_target, 'r') as f:
            export_content = json.load(f)
            self.assertIsInstance(export_content, dict)

        with open(self.storage_file, 'r') as f:
            storage_content = json.load(f)
            self.assertIsInstance(storage_content, dict)

    def test_market_portfolio_liquidity_scenario_analyzer_class_integration(self):
        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(
            storage_file=self.storage_file
        )

        result = analyzer.evaluate_portfolio(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_result", result)
        self.assertIn("stress_result", result)

        self.assertTrue(os.path.exists(self.export_target), "Export target file must be created by class method")
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by class method")

        reserve_calc = analyzer._calculate_required_reserve(100.0, 200.0)
        self.assertEqual(reserve_calc, 230.0)

if __name__ == "__main__":
    unittest.main()