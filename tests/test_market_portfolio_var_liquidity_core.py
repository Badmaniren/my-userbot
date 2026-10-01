import unittest
import io
import json
import os
import uuid
import random
from unittest.mock import patch, mock_open
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.portfolio_id = uuid.uuid4().hex
        self.confidence = round(random.uniform(0.8, 0.99), 2)
        self.export_path = f"{uuid.uuid4().hex}.json"

    def test_start_new_io_stream_handling(self):
        random_content = uuid.uuid4().hex
        stream = io.BytesIO(random_content.encode('utf-8'))
        
        result = start_new(input_stream=stream)
        self.assertEqual(result, random_content)

    def test_start_new_db_storage_passthrough(self):
        random_db_ref = uuid.uuid4().hex
        result = start_new(db_storage=random_db_ref)
        self.assertEqual(result, random_db_ref)

    def test_calculate_var_and_liquidity_logic(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence
        )
        
        expected_var = round(1500.50 * self.confidence, 2)
        
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_value"], expected_var)
        self.assertIsInstance(result["liquidity_score"], float)

    def test_export_functionality_with_mock(self):
        with patch("builtins.open", mock_open()) as mocked_file:
            self.core.calculate_var_and_liquidity(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence,
                export_target=self.export_path
            )
            
            mocked_file.assert_called_once_with(self.export_path, "w", encoding="utf-8")
            
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)
            
            self.assertEqual(parsed_data["portfolio_id"], self.portfolio_id)
            self.assertEqual(parsed_data["var_value"], round(1500.50 * self.confidence, 2))

    def test_default_return_on_empty_args(self):
        result = start_new()
        self.assertEqual(result, {"status": "success"})

    def tearDown(self):
        if os.path.exists(self.export_path):
            os.remove(self.export_path)

if __name__ == "__main__":
    unittest.main()