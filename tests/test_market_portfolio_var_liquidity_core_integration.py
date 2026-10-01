import unittest
import os
import uuid
import random
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_net if False else start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_filename = f"export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_integration_calculation_and_export(self):
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)

        self.assertTrue(os.path.exists(self.export_filename), "Файл экспорта должен быть создан в ходе интеграционного взаимодействия.")
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(file_data.get("var_value"), result.get("var_value"))
            self.assertEqual(file_data.get("liquidity_score"), result.get("liquidity_score"))

    def test_integration_storage_dependency(self):
        random_storage_payload = f"storage_state_{uuid.uuid4()}"
        response = start_new(db_storage=random_storage_payload)
        self.assertEqual(response, random_storage_payload)

if __name__ == "__main__":
    unittest.main()