import os
import json
import uuid
import random
import unittest
from skills import market_portfolio_liquidity_scenario_analyzer
from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(10, 99)}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        
        self.export_target = f"test_exports_{uuid.uuid4().hex[:6]}/var_export.json"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:6]}/stress_storage.json"

    def tearDown(self):
        for path in [self.export_target, self.storage_file]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            if path and not str(path).startswith("s3://"):
                dir_name = os.path.dirname(path)
                if dir_name and os.path.exists(dir_name):
                    try:
                        os.rmdir(dir_name)
                    except OSError:
                        pass

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

        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.export_target, 'r') as f:
            export_content = json.load(f)
        self.assertIsInstance(export_content, dict)

        with open(self.storage_file, 'r') as f:
            storage_content = json.load(f)
        self.assertIsInstance(storage_content, dict)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(
            storage_file=self.storage_file
        )

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
        self.assertTrue(os.path.exists(self.export_target))

if __name__ == "__main__":
    unittest.main()