import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"test_export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass

    def test_integration_calculation_and_export(self):
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

        self.assertTrue(os.path.exists(self.export_target), "Экспортный файл не был создан в процессе интеграции")

        with open(self.export_target, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(file_data.get("var_value"), expected_var)
        self.assertEqual(file_data.get("liquidity_score"), 0.85)

    def sf_test_db_storage_integration(self):
        dummy_storage = f"db_conn_{uuid.uuid4()}"
        res = start_new(db_storage=dummy_storage)
        self.assertEqual(res, dummy_storage)

if __name__ == "__main__":
    unittest.main()