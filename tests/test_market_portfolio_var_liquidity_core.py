import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
import string

from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.core_instance = market_portfolio_var_liquidity_core()

    def test_bytes_io_handling(self):
        random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        bytes_stream = io.BytesIO(random_text.encode('utf-8'))
        
        result = start_new(payload=bytes_stream)
        self.assertEqual(result, random_text)

    def test_db_storage_handling(self):
        random_storage_val = ''.join(random.choices(string.ascii_letters, k=16))
        result = start_new(db_storage=random_storage_val)
        self.assertEqual(result, random_storage_val)

    def test_portfolio_calculation_default_confidence(self):
        portfolio_id = uuid.uuid4().hex
        result = start_new(portfolio_id=portfolio_id)
        
        expected_var = round(1500.50 * 0.95, 2)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

    def test_portfolio_calculation_custom_confidence(self):
        portfolio_id = uuid.uuid4().hex
        confidence = round(random.uniform(0.50, 0.99), 2)
        
        result = self.core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence
        )
        
        expected_var = round(1500.50 * confidence, 2)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), 0.85)

    def test_portfolio_calculation_with_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence = round(random.uniform(0.80, 0.99), 2)
        export_target = f"{uuid.uuid4().hex}.json"
        
        try:
            with patch("builtins.open", create=True) as mock_open:
                mock_file = mock_open.return_value.__enter__.return_value
                
                result = start_new(
                    portfolio_id=portfolio_id,
                    confidence_level=confidence,
                    export_target=export_target
                )
                
                mock_open.assert_called_once_with(export_target, "w", encoding="utf-8")
                mock_file.write.assert_called()
                
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["var_value"], round(1500.50 * confidence, 2))
        finally:
            if os.path.exists(export_target):
                try:
                    os.remove(export_target)
                except OSError:
                    pass

    def test_default_fallback_return(self):
        random_arg_name = uuid.uuid4().hex
        random_arg_val = uuid.uuid4().hex
        
        kwargs = {random_arg_name: random_arg_val}
        result = start_new(**kwargs)
        
        self.assertEqual(result, {"status": "success"})


if __name__ == '__main__':
    unittest.main()