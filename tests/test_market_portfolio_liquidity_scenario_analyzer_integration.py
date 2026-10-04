import unittest
import os
import json
import uuid
import random
from skills import market_portfolio_liquidity_scenario_analyzer

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.symbol = f"ASSET_{random.randint(100, 999)}"
        self.percentage = round(random.uniform(0.05, 0.30), 2)
        self.shifts = [round(random.uniform(-0.1, -0.01), 2), round(random.uniform(0.01, 0.1), 2)]
        
        self.export_target = f"test_output_{uuid.uuid4()}.json"
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"

    def tearDown(self):
        for path in [self.export_target, self.storage_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
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
        self.assertIn("reserve_capital_requirement", result)
        self.assertIn("var_liquidity_data", result)
        self.assertIn("stress_pipeline_data", result)

        self.assertTrue(os.path.exists(self.export_target), "Файл экспорта VaR не был создан")
        with open(self.export_target, 'r') as f:
            export_data = json.load(f)
            self.assertIsInstance(export_data, dict)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища стресс-пайплайна не был создан")
        with open(self.storage_file, 'r') as f:
            storage_data = json.load(f)
            self.assertIsInstance(storage_data, dict)

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

        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

        reserve = analyzer._calculate_required_reserve(100.0, 200.0)
        self.assertEqual(reserve, 230.0)

if __name__ == "__main__":
    unittest.main()