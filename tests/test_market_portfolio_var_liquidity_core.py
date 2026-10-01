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

    def test_bytes_io_handling(self):
        random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        byte_stream = io.BytesIO(random_text.encode('utf-8'))
        random_key = ''.join(random.choices(string.ascii_lowercase, k=10))
        
        result = start_new(**{random_key: byte_stream})
        self.assertEqual(result, random_text)

    def test_db_storage_handling(self):
        random_db_value = f"db_node_{uuid.uuid4().hex}"
        result = start_new(db_storage=random_db_value)
        self.assertEqual(result, random_db_value)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_filename = f"export_{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_filename
            )
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            expected_var = round(1500.50 * confidence_level, 2)
            self.assertAlmostEqual(result["var_value"], expected_var)
            self.assertIn("liquidity_score", result)
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            self.assertEqual(loaded_data["portfolio_id"], portfolio_id)
            self.assertEqual(loaded_data["var_value"], expected_var)
            
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_default_success_status(self):
        random_extra_param = f"param_{uuid.uuid4().hex}"
        result = start_new(**{random_extra_param: random.randint(1, 100)})
        self.assertEqual(result, {"status": "success"})

    def test_class_wrapper_method(self):
        portfolio_id = f"cls_port_{uuid.uuid4().hex}"
        confidence_level = round(random.uniform(0.50, 0.95), 2)
        
        core_instance = market_portfolio_var_liquidity_core()
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level
        )
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertAlmostEqual(result["var_value"], round(1500.50 * confidence_level, 2))


if __name__ == '__main__':
    unittest.main()