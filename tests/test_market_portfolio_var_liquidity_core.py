import unittest
from unittest.mock import patch, mock_open
import io
import json
import os
import random
import uuid
import string

from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core

class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_start_new_bytes_io(self):
        random_suffix = uuid.uuid4().hex
        random_text = f"test_payload_{random_suffix}"
        byte_stream = io.BytesIO(random_text.encode('utf-8'))
        
        random_key = uuid.uuid4().hex
        kwargs = {random_key: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, random_text)

    def test_start_new_db_storage_single(self):
        random_storage_val = uuid.uuid4().hex
        result = start_new(db_storage=random_storage_val)
        self.assertEqual(result, random_storage_val)

    def test_start_new_portfolio_calculation(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        
        result = start_new(portfolio_id=portfolio_id, confidence_level=confidence_level)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        
        expected_var = round(1500.50 * confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertIn("liquidity_score", result)

    def test_start_new_portfolio_with_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.80, 0.99), 2)
        export_target = f"{uuid.uuid4().hex}.json"
        
        mock_file_handle = mock_open()
        with patch("builtins.open", mock_file_handle):
            result = start_new(
                portfolio_id=portfolio_id, 
                confidence_level=confidence_level, 
                export_target=export_target
            )
            
        mock_file_handle.assert_called_once_with(export_target, "w", encoding="utf-8")
        self.assertEqual(result.get("portfolio_id"), portfolio_id)

    def test_start_new_default_success(self):
        random_noise_key = uuid.uuid4().hex
        random_noise_val = uuid.uuid4().hex
        result = start_new(**{random_noise_key: random_noise_val})
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_class_calculate_var_and_liquidity(self):
        core_instance = market_portfolio_var_liquidity_core()
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.85, 0.98), 2)
        export_target = f"{uuid.uuid4().hex}.json"
        
        mock_file_handle = mock_open()
        with patch("builtins.open", mock_file_handle):
            result = core_instance.calculate_var_and_liquidity(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target
            )
            
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["var_value"], round(1500.50 * confidence_level, 2))

if __name__ == "__main__":
    unittest.main()