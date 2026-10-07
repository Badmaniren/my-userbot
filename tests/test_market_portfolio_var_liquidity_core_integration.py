import json
import os
import random
import tempfile
import unittest
import uuid

try:
    from skills.market_portfolio_var_liquidity_core import (
        market_portfolio_var_liquidity_core,
        start_new,
    )
except ImportError:
    from market_portfolio_var_liquidity_core import (
        market_portfolio_var_liquidity_core,
        start_new,
    )


class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = market_portfolio_var_liquidity_core()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_var_and_liquidity_calculation_and_file_export(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex}"
        random_confidence = round(random.uniform(0.80, 0.99), 4)
        export_filename = f"export_{uuid.uuid4().hex}.json"
        export_path = os.path.join(self.temp_dir.name, export_filename)

        result = self.engine.calculate_var_and_liquidity(
            portfolio_id=random_portfolio_id,
            confidence_level=random_confidence,
            export_target=export_path,
        )

        expected_var = round(1500.50 * random_confidence, 2)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

        self.assertTrue(
            os.path.exists(export_path),
            f"Файл экспорта {export_path} должен быть создан",
        )

        with open(export_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(persisted_data.get("var_value"), expected_var)
        self.assertEqual(persisted_data.get("liquidity_score"), 0.85)

    def test_start_new_direct_invocation_without_export(self):
        random_portfolio_id = f"port_{uuid.uuid4().hex}"
        random_confidence = round(random.uniform(0.50, 0.79), 3)

        result = start_new(
            portfolio_id=random_portfolio_id,
            confidence_level=random_confidence,
        )

        expected_var = round(1500.50 * random_confidence, 2)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

    def test_start_new_db_storage_pass_through(self):
        random_token = f"db_conn_{uuid.uuid4().hex}"
        result = start_new(db_storage=random_token)
        self.assertEqual(result, random_token)


if __name__ == "__main__":
    unittest.main()