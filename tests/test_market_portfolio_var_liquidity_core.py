import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_bytes_io_handling(self):
        random_text = f"risk_shock_{uuid.uuid4().hex}"
        byte_stream = io.BytesIO(random_text.encode('utf-8'))
        
        random_key = f"stream_{uuid.uuid4().hex}"
        kwargs = {random_key: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, random_text)

    def test_db_storage_handling(self):
        storage_payload = {
            "node_id": uuid.uuid4().hex,
            "liquidity_reserve": random.uniform(1000.0, 50000.0)
        }
        
        result = start_new(db_storage=storage_payload)
        self.assertEqual(result, storage_payload)

    def test_portfolio_calculation_default_confidence(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        
        result = start_new(portfolio_id=portfolio_id)
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], round(1500.50 * 0.95, 2))
        self.assertEqual(result["liquidity_score"], 0.85)

    def test_portfolio_ calculation_custom_confidence_and_export(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        confidence = round(random.uniform(0.80, 0.99), 2)
        export_filename = f"{uuid.uuid4().hex}.json"
        
        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence,
                export_target=export_filename
            )
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["var_value"], round(1500.50 * confidence, 2))
            
            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                self.assertEqual(loaded_data["portfolio_id"], portfolio_id)
                self.assertEqual(loaded_data["var_value"], round(1500.50 * confidence, 2))
                self.assertEqual(loaded_data["liquidity_score"], 0.85)
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_default_success_status(self):
        random_garbage = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = start_new(**random_garbage)
        self.assertEqual(result, {"status": "success"})

    def test_class_wrapper_method(self):
        core_instance = market_portfolio_var_liquidity_core()
        portfolio_id = f"cls_port_{uuid.uuid4().hex}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        
        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence
        )
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], round(1500.50 * confidence, 2))
        self.assertEqual(result["liquidity_score"], 0.85)


if __name__ == "__main__":
    unittest.main()