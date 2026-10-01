import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_start_new_default_success(self):
        result = start_new()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def func_test_bytes_io_handling(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        byte_stream = io.BytesIO(random_bytes)
        random_param_name = uuid.uuid4().hex
        
        kwargs = {random_param_name: byte_stream}
        result = start_new(**kwargs)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, random_bytes.decode('utf-8'))

    def test_db_storage_handling(self):
        random_storage_value = uuid.uuid4().hex
        result = start_new(db_storage=random_storage_value)
        self.assertEqual(result, random_storage_value)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_filename = f"{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_filename
            )
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            
            expected_var = round(1500.50 * confidence_level, 2)
            self.assertEqual(result["var_value"], expected_var)
            self.assertIn("liquidity_score", result)
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                
            self.assertEqual(loaded_data["portfolio_id"], portfolio_id)
            self.assertEqual(loaded_data["var_value"], expected_var)
            
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_class_method_var_and_liquidity(self):
        core_instance = market_portfolio_var_liquidity_core()
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.70, 0.98), 2)
        
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), round(1500.50 * confidence_level, 2))


if __name__ == '__main__':
    unittest.main()