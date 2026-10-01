import unittest
import os
import uuid
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = 0.99
        self.export_filename = f"test_export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_direct(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)
        self.assertEqual(result.get("var_value"), round(1500.50 * self.confidence_level, 2))

    def test_calculate_var_with_export_target(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )
        self.assertTrue(os.path.exists(self.export_filename))
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertEqual(data.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(data.get("var_value"), result.get("var_value"))
        self.assertEqual(data.get("liquidity_score"), result.get("liquidity_score"))

    def test_start_new_function_storage(self):
        storage_id = f"db-{uuid.uuid4()}"
        res = start_new(db_storage=storage_id)
        self.assertEqual(res, storage_id)

if __name__ == "__main__":
    unittest.main()