import unittest
from unittest.mock import patch
import io
import os
import json
import random
import uuid
import string

from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_bytes_io_handling(self):
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        byte_stream = io.BytesIO(random_chars.encode('utf-8'))
        
        param_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        kwargs = {param_name: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, random_chars)

    def_name = 'test_db_storage_isolation'
    def test_db_storage_isolation(self):
        storage_val = uuid.uuid4().hex
        kwargs = {"db_storage": storage_val}
        
        result = start_new(**kwargs)
        self.assertEqual(result, storage_val)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_filename = f"{uuid.uuid4().hex}.json"
        
        try:
            core = market_portfolio_var_liquidity_core()
            result = core.calculate_var_and_liquidity(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_filename
            )
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            expected_var = round(1500.50 * confidence_level, 2)
            self.assertEqual(result["var_value"], expected_var)
            self.assertEqual(result["liquidity_score"], 0.85)
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                
            self.assertEqual(loaded_data["portfolio_id"], portfolio_id)
            self.assertEqual(loaded_data["var_value"], expected_var)
            self.assertEqual(loaded_data["liquidity_score"], 0.85)
            
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_default_success_return(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        result = start_new(**{random_key: random_val})
        self.assertEqual(result, {"status": "success"})


if __name__ == '__main__':
    unittest.main()