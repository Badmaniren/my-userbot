import unittest
import os
import uuid
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = 0.98
        self.export_filename = f"test_export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        
        expected_var = round(1500.50 * self.confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertIn("liquidity_score", result)

        self.assertTrue(os.path.exists(self.export_filename), "Файл экспорта не был создан.")
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            
        self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(file_data.get("var_value"), expected_var)

if __name__ == "__main__":
    unittest.main()