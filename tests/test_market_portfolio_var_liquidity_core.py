import unittest
from unittest.mock import patch
import io
import os
import json
import uuid
import random
import string

from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_confidence = round(random.uniform(0.80, 0.99), 2)
        self.random_storage_val = uuid.uuid4().hex

    def test_start_new_bytes_io_handling(self):
        random_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        random_kwarg_name = f"stream_{uuid.uuid4().hex[:6]}"
        
        result = start_new(**{random_kwarg_name: stream})
        self.assertEqual(result, random_bytes.decode('utf-8'))

    def test_start_new_db_storage_single_arg(self):
        result = start_new(db_storage=self.random_storage_val)
        self.assertEqual(result, self.random_storage_val)

    def test_start_new_db_storage_multiple_args(self):
        extra_key = f"key_{uuid.uuid4().hex[:6]}"
        extra_val = uuid.uuid4().hex
        result = start_new(db_storage=self.random_storage_val, **{extra_key: extra_val})
        self.assertEqual(result, self.random_storage_val)

    def test_start_new_portfolio_calculation(self):
        result = start_new(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        
        expected_var = round(1500.50 * self.random_confidence, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

    def test_start_new_with_export_target(self):
        export_filename = f"{uuid.uuid4().hex}.json"
        try:
            result = start_new(
                portfolio_id=self.random_portfolio_id,
                confidence_level=self.random_confidence,
                export_target=export_filename
            )
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            
            self.assertEqual(file_data.get("portfolio_id"), self.random_portfolio_id)
            self.assertEqual(file_data.get("var_value"), result.get("var_value"))
            self.assertEqual(file_data.get("liquidity_score"), result.get("liquidity_score"))
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_start_new_default_success(self):
        random_param_key = f"param_{uuid.uuid4().hex[:6]}"
        random_param_val = uuid.uuid4().hex
        result = start_new(**{random_param_key: random_param_val})
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_class_calculate_var_and_liquidity(self):
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        expected_var = round(1500.50 * self.random_confidence, 2)
        self.assertEqual(result.get("var_value"), expected_var)


if __name__ == '__main__':
    unittest.main()