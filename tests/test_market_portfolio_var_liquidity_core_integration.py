import unittest
import os
import uuid
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):

    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.test_portfolio_id = f"port_{uuid.uuid4().hex}"
        self.confidence_level = round(0.90 + (uuid.uuid4().int % 10) / 100, 2)
        self.export_filename = f"export_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.test_portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.test_portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)
        
        expected_var = round(1500.50 * self.confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)

        self.assertTrue(os.path.exists(self.export_filename), "Экспортный файл не был создан")
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            
        self.assertEqual(file_data.get("portfolio_id"), self.test_portfolio_id)
        self.assertEqual(file_data.get("var_value"), expected_var)
        self.assertEqual(file_data.get("liquidity_score"), result.get("liquidity_score"))

    def test_start_new_direct_call_storage(self):
        random_storage_val = f"storage_{uuid.uuid4().hex}"
        res = start_new(db_storage=random_storage_val)
        self.assertEqual(res, random_storage_val)

if __name__ == "__main__":
    unittest.main()