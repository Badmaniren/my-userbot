import unittest
from unittest.mock import patch
import io
import json
import uuid
import random
import os

from skills.market_portfolio_var_liquidity_core import (
    start_new,
    market_portfolio_var_liquidity_core
)

class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_bytes_io_processing(self):
        random_text = f"risk_metric_{uuid.uuid4().hex}"
        bytes_stream = io.BytesIO(random_text.encode('utf-8'))
        
        result = start_new(payload_stream=bytes_stream)
        self.assertEqual(result, random_text)

    def test_db_storage_handling(self):
        storage_id = f"db_conn_{uuid.uuid4().hex}"
        result = start_new(db_storage=storage_id)
        self.assertEqual(result, storage_id)

    def test_portfolio_calculation_and_export(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        export_target = f"report_{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence,
                export_target=export_target
            )
            
            expected_var = round(1500.50 * confidence, 2)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["var_value"], expected_var)
            self.assertEqual(result["liquidity_score"], 0.85)
            
            self.assertTrue(os.path.exists(export_target))
            with open(export_target, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data["portfolio_id"], portfolio_id)
                self.assertEqual(data["var_value"], expected_var)
        finally:
            if os.path.exists(export_target):
                os.remove(export_target)

    def test_default_success_status(self):
        random_arg = uuid.uuid4().hex
        result = start_new(unknown_parameter=random_arg)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_class_wrapper_method(self):
        portfolio_id = f"port_cls_{uuid.uuid4().hex}"
        confidence = round(random.uniform(0.80, 0.98), 2)
        
        core_instance = market_portfolio_var_liquidity_core()
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence
        )
        
        expected_var = round(1500.50 * confidence, 2)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], expected_var)

if __name__ == '__main__':
    unittest.main()