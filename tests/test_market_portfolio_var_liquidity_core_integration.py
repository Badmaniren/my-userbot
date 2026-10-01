import unittest
import uuid
import random
import os
import json
import io
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    
    def setUp(self):
        self.core_class = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_filename = f"export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core_class.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        
        expected_var = round(1500.50 * self.confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)
        
        self.assertTrue(os.path.exists(self.export_filename))
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            
        self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(file_data.get("var_value"), expected_var)

    def direct_start_new_bytes_io_integration(self):
        random_string = f"data-stream-{uuid.uuid4()}"
        byte_stream = io.BytesIO(random_string.encode('utf-8'))
        
        res = start_new(payload_stream=byte_stream)
        self.assertEqual(res, random_string)

    def test_db_storage_pass_through(self):
        storage_id = f"db-{uuid.uuid4()}"
        res = start_new(db_storage=storage_id)
        self.assertEqual(res, storage_id)

if __name__ == '__main__':
    unittest.main()