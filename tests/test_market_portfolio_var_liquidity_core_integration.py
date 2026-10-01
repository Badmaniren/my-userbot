import unittest
import uuid
import random
import os
import json
import io

from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()
        self.portfolio_id = str(uuid.uuid4())
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"test_export_{uuid.uuid4()}.json"

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

        self.assertTrue(os.path.exists(self.export_target))
        with open(self.export_target, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(file_data.get("var_value"), expected_var)
            self.assertEqual(file_data.get("liquidity_score"), result.get("liquidity_score"))

    def test_start_new_with_db_storage(self):
        mock_db_value = f"db_conn_{uuid.uuid4()}"
        res = start_new(db_storage=mock_db_value)
        self.assertEqual(res, mock_db_value)

    def test_start_new_with_bytes_io(self):
        random_text = f"stream_data_{uuid.uuid4()}"
        byte_stream = io.BytesIO(random_text.encode('utf-8'))
        res = start_new(stream_flow=byte_stream)
        self.assertEqual(res, random_text)

    def test_start_new_default_success(self):
        res = start_new()
        self.assertEqual(res, {"status": "success"})

if __name__ == "__main__":
    unittest.main()