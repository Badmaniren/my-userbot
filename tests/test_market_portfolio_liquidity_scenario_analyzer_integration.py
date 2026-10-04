import unittest
import os
import uuid
import random
from skills.market_portfolio_liquidity_scenario_analyzer import analyze_liquidity_stress_scenarios

class TestMarketPortfolioLiquidityScenarioAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
        self.confidence_level = round(random.uniform(0.95, 0.99), 4)
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.storage_file = f"test_stress_storage_{uuid.uuid4().hex[:6]}.json"
        self.export_target = f"test_export_{uuid.uuid4().hex[:6]}.json"

    def tearDown(self):
        for file_path in [self.storage_file, self.export_target]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_liquidity_scenario_analyzer_composition(self):
        result = analyze_liquidity_stress_scenarios(
            portfolio_id=self.portfolio_id,
            symbol=self.symbol,
            confidence_level=self.confidence_level,
            percentage=self.percentage,
            shifts=self.shifts,
            storage_file=self.storage_file,
            export_target=self.export_target
        )

        self.assertIsInstance(result, dict)
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)

        self.assertIn("var_liquidity_data", result)
        self.assertIn("stress_scenario_data", result)
        self.assertIn("capital_reserve_requirement", result)

        self.assertTrue(
            os.path.exists(self.storage_file),
            f"Ожидается создание файла хранилища пайплайна стресс-сценариев: {self.storage_file}"
        )
        
        self.assertTrue(
            os.path.exists(self.export_target),
            f"Ожидается формирование целевого файла экспорта VaR и ликвидности: {self.export_target}"
        )

if __name__ == "__main__":
    unittest.main()