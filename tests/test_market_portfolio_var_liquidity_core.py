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
        self.random_portfolio_id = f"port_{uuid.uuid4().hex}"
        self.random_db_storage = f"db_{uuid.uuid4().hex}"
        self.random_bytes_content = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        self.random_export_filename = f"export_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_export_filename):
            try:
                os.remove(self.random_export_filename)
            except OSError:
                pass

    def test_start_new_bytes_io_handling(self):
        stream = io.BytesIO(self.random_bytes_content)
        random_arg_name = f"stream_{uuid.uuid4().hex}"
        kwargs = {random_arg_name: stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, self.random_bytes_content.decode('utf-8', errors='ignore'))

    def test_start_new_db_storage_priority(self):
        kwargs = {
            "db_storage": self.random_db_storage,
            "portfolio_id": self.random_portfolio_id,
            "confidence_level": random.uniform(0.8, 0.99)
        }
        
        result = start_new(**kwargs)
        self.assertEqual(result, self.random_db_storage)

    def test_start_new_portfolio_calculation_and_export(self):
        confidence = round(random.uniform(0.80, 0.99), 2)
        expected_var = round(1500.50 * confidence, 2)
        
        result = start_new(
            portfolio_id=self.random_portfolio_id,
            confidence_level=confidence,
            export_target=self.random_export_filename
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertEqual(result["var_value"], expected_var)
        self.assertEqual(result["liquidity_score"], 0.85)
        
        self.assertTrue(os.path.exists(self.random_export_filename))
        with open(self.random_export_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["portfolio_id"], self.random_portfolio_id)
            self.assertEqual(data["var_value"], expected_var)

    def test_start_new_default_success_status(self):
        random_garbage_key = f"garbage_{uuid.uuid4().hex}"
        random_garbage_value = uuid.uuid4().hex
        
        result = start_new(**{random_garbage_key: random_garbage_value})
        self.assertEqual(result, {"status": "success"})

    def test_class_calculate_var_and_liquidity(self):
        confidence = round(random.uniform(0.80, 0.99), 2)
        expected_var = round(1500.50 * confidence, 2)
        
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=confidence,
            export_target=None
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertEqual(result["var_value"], expected_var)
        self.assertEqual(result["liquidity_score"], 0.85)

    def test_class_calculate_var_and_liquidity_with_export(self):
        confidence = round(random.uniform(0.80, 0.99), 2)
        
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=confidence,
            export_target=self.random_export_filename
        )
        
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertTrue(os.path.exists(self.random_export_filename))

    def test_start_new_default_confidence_level(self):
        expected_var = round(1500.50 * 0.95, 2)
        
        result = start_new(portfolio_id=self.random_portfolio_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertEqual(result["var_value"], expected_var)
        self.assertEqual(result["liquidity_score"], 0.85)

if __name__ == '__main__':
    unittest.main()