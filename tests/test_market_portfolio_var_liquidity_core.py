import unittest
from unittest.mock import patch, mock_open
import io
import json
import random
import uuid
import string

from skills.market_portfolio_var_liquidity_core import (
    start_new,
    market_portfolio_var_liquidity_core
)


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.db_storage_val = f"db_{uuid.uuid4().hex}"
        self.export_path = f"export_{uuid.uuid4().hex[:6]}.json"

    def test_start_new_bytes_io_handling(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=16)).encode("utf-8")
        byte_stream = io.BytesIO(random_bytes)
        
        param_name = f"stream_{uuid.uuid4().hex[:4]}"
        kwargs = {param_name: byte_stream}
        
        result = start_new(**kwargs)
        self.assertEqual(result, random_bytes.decode("utf-8"))

    def test_start_new_db_storage_handling(self):
        kwargs = {"db_storage": self.db_storage_val, "unrelated_param": uuid.uuid4().hex}
        result = start_new(**kwargs)
        self.assertEqual(result, self.db_storage_val)

    def test_start_new_portfolio_calculation_and_export(self):
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = start_new(
                    portfolio_id=self.portfolio_id,
                    confidence_level=self.confidence_level,
                    export_target=self.export_path
                )
                
                expected_var = round(1500.50 * self.confidence_level, 2)
                
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertEqual(result["var_value"], expected_var)
                self.assertEqual(result["liquidity_score"], 0.85)
                
                mock_file.assert_called_once_with(self.export_path, "w", encoding="utf-8")
                mock_json_dump.assert_called_once()

    def test_start_new_default_success(self):
        unrelated_arg = uuid.uuid4().hex
        result = start_new(random_key=unrelated_arg)
        self.assertEqual(result, {"status": "success"})

    def test_class_calculate_var_and_liquidity(self):
        core_instance = market_portfolio_var_liquidity_core()
        
        with patch("skills.market_portfolio_var_liquidity_core.start_new") as mock_start_new:
            expected_dict = {
                "portfolio_id": self.portfolio_id,
                "var_value": round(1500.50 * self.confidence_level, 2),
                "liquidity_score": 0.85
            }
            mock_start_new.return_value = expected_dict
            
            res = core_instance.calculate_var_and_liquidity(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_path
            )
            
            mock_start_new.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_path
            )
            self.assertEqual(res, expected_dict)


if __name__ == "__main__":
    unittest.main()