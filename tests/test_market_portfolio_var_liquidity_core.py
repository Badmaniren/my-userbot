import unittest
from unittest.mock import patch
import io
import os
import json
import uuid
import random
import string

from skills.market_portfolio_var_liquidity_core import (
    start_new,
    market_portfolio_var_liquidity_core
)


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_bytes_io_handling(self):
        rand_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        byte_stream = io.BytesIO(rand_string.encode('utf-8'))
        
        random_key = uuid.uuid4().hex
        kwargs = {random_key: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, rand_string)

    def test_db_storage_single_arg(self):
        random_storage = uuid.uuid4().hex
        result = start_new(db_storage=random_storage)
        self.assertEqual(result, random_storage)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_target = f"test_export_{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target
            )
            
            expected_var = round(1500.50 * confidence_level, 2)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("var_value"), expected_var)
            self.assertIn("liquidity_score", result)
            
            self.assertTrue(os.path.exists(export_target))
            with open(export_target, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.assertEqual(loaded_data.get("portfolio_id"), portfolio_id)
                self.assertEqual(loaded_data.get("var_value"), expected_var)
        finally:
            if os.path.exists(export_target):
                os.remove(export_target)

    def test_default_success_status(self):
        random_key = uuid.uuid4().hex
        random_value = uuid.uuid4().hex
        result = start_new(**{random_key: random_value})
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_class_wrapper_interface(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.85, 0.98), 2)
        
        core_instance = market_portfolio_var_liquidity_core()
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level
        )
        
        expected_var = round(1500.50 * confidence_level, 2)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)


if __name__ == "__main__":
    unittest.main()