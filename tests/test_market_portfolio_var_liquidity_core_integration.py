import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):

    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.random_portfolio_id = f"port_{uuid.uuid4().hex}"
        self.random_confidence = round(random.uniform(0.90, 0.99), 2)
        self.export_filename = f"test_export_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence,
            export_target=self.export_filename
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        
        expected_var = round(1500.50 * self.random_confidence, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

        self.assertTrue(os.path.exists(self.export_filename), "Файл экспорта не был создан в процессе интеграции")

        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("portfolio_id"), self.random_portfolio_id)
            self.assertEqual(file_data.get("var_value"), expected_var)

    def test_start_new_db_storage_integration(self):
        random_db_payload = f"db_state_{uuid.uuid4().hex}"
        response = start_new(db_storage=random_db_payload)
        self.assertEqual(response, random_db_payload)

if __name__ == "__main__":
    unittest.main()