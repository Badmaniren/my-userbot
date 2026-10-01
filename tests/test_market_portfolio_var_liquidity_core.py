import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()

    def test_start_new_default_success(self):
        result = start_new()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_bytes_io_handling(self):
        random_payload = uuid.uuid4().bytes + b"_" + uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_payload)
        param_name = f"stream_{uuid.uuid4().hex[:6]}"
        
        result = start_new(**{param_name: stream})
        self.assertEqual(result, random_payload.decode('utf-8', errors='ignore'))

    def test_db_storage_handling(self):
        random_db_identifier = f"db_cluster_{uuid.uuid4().hex}"
        result = start_new(db_storage=random_db_identifier)
        self.assertEqual(result, random_db_identifier)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_target = f"{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target
            )
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            
            expected_var = round(1500.50 * confidence_level, 2)
            self.assertEqual(result.get("var_value"), expected_var)
            self.assertEqual(result.get("liquidity_score"), 0.85)
            
            self.assertTrue(os.path.exists(export_target))
            with open(export_target, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.assertEqual(loaded_data.get("portfolio_id"), portfolio_id)
                self.assertEqual(loaded_data.get("var_value"), expected_var)
        finally:
            if os.path.exists(export_target):
                os.remove(export_target)

    def test_class_method_var_and_liquidity(self):
        portfolio_id = f"acc_{uuid.uuid4().hex[:10]}"
        confidence_level = round(random.uniform(0.5, 0.99), 2)
        
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), round(1500.50 * confidence_level, 2))


if __name__ == "__main__":
    unittest.main()