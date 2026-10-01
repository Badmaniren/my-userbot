import unittest
import uuid
import random
import os
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"export_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core_instance.calculate_var_and_liquidity(
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

        self.assertTrue(os.path.exists(self.export_target), "Экспортный файл должен быть создан в процессе интеграционного вызова")
        
        with open(self.export_target, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(file_data.get("var_value"), expected_var)

    def test_start_new_storage_integration(self):
        storage_payload = f"storage_data_{uuid.uuid4().hex}"
        response = start_new(db_storage=storage_payload)
        self.assertEqual(response, storage_payload)

if __name__ == '__main__':
    unittest.main()