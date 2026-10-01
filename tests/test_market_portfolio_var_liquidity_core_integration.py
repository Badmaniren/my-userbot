import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)
        
        expected_var = round(1500.50 * self.confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)

        self.assertTrue(os.path.exists(self.export_target))
        with open(self.export_target, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(data.get("var_value"), expected_var)

    def test_start_new_direct_invocation(self):
        random_storage = f"storage-{uuid.uuid4()}"
        res = start_new(db_storage=random_storage)
        self.assertEqual(res, random_storage)

if __name__ == "__main__":
    unittest.main()