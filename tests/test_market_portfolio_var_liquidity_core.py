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

    def test_start_new_bytes_io_handling(self):
        rand_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        byte_stream = io.BytesIO(rand_string.encode('utf-8'))
        
        random_key = uuid.uuid4().hex
        kwargs = {random_key: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, rand_string)

    def test_start_new_db_storage_isolation(self):
        db_token = uuid.uuid4().hex
        result = start_new(db_storage=db_token)
        self.assertEqual(result, db_token)

    def test_start_new_portfolio_calculation(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.5, 0.99), 2)
        
        result = start_new(portfolio_id=portfolio_id, confidence_level=confidence_level)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], round(1500.50 * confidence_level, 2))
        self.assertEqual(result["liquidity_score"], 0.85)

    def test_start_new_portfolio_with_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.5, 0.99), 2)
        export_filename = f"{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id, 
                confidence_level=confidence_level, 
                export_target=export_filename
            )
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.assertEqual(data["portfolio_id"], portfolio_id)
            self.assertEqual(data["var_value"], round(1500.50 * confidence_level, 2))
            self.assertEqual(data["liquidity_score"], 0.85)
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_start_new_default_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        result = start_new(**{rand_key: rand_val})
        self.assertEqual(result, {"status": "success"})

    def test_class_calculate_var_and_liquidity(self):
        core_instance = market_portfolio_var_liquidity_core()
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.1, 0.9), 2)
        
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], round(1500.50 * confidence_level, 2))
        self.assertEqual(result["liquidity_score"], 0.85)

if __name__ == '__main__':
    unittest.main()