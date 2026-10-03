import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import os

from skills.market_portfolio_macro_liquidity_tracker import start_new, market_portfolio_macro_liquidity_tracker

class TestMarketPortfolioMacroLiquidityTracker(unittest.TestCase):

    def test_start_new_with_db_macro_data(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        expected_dict = {rand_key: rand_val}

        mock_db = MagicMock()
        mock_db.fetch_macro_data.return_value = expected_dict

        dependencies = {"db_storage": mock_db}
        result = start_new(dependencies)

        self.assertEqual(result, expected_dict)
        mock_db.fetch_macro_data.assert_called_once()

    def test_start_new_with_parser_stream(self):
        rand_parsed_val = uuid.uuid4().hex
        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = rand_parsed_val

        dependencies = {"market_parser": mock_parser}
        result = start_new(dependencies)

        self.assertEqual(result.get("status"), "stream_processed")
        self.assertEqual(result.get("value"), rand_parsed_val)
        mock_parser.parse_stream.assert_called_once()

    def test_start_new_with_valuation_calculate(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(10, 500)
        expected_dict = {rand_key: rand_val, uuid.uuid4().hex: "val"}

        mock_valuation = MagicMock()
        mock_valuation.calculate.return_value = expected_dict

        dependencies = {"market_portfolio_valuation": mock_valuation}
        result = start_new(dependencies)

        self.assertEqual(result, expected_dict)
        mock_valuation.calculate.assert_called_once()

    def test_start_new_default_fallback(self):
        dependencies = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = start_new(dependencies)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("value", result)
        self.assertTrue(any(isinstance(k, str) and len(k) > 10 for k in result.keys()))

    def test_market_portfolio_macro_liquidity_tracker_integration(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_liquidity = random.uniform(50.0, 9999.9)

        tracker_input = {
            "portfolio_id": rand_portfolio_id,
            "target_liquidity": rand_liquidity
        }

        mock_db_func = MagicMock()
        with patch("skills.market_portfolio_macro_liquidity_tracker.db_storage", mock_db_func):
            result = market_portfolio_macro_liquidity_tracker(tracker_input)

        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("liquidity"), rand_liquidity)

        expected_log_path = f"logs/macro_liquidity_{rand_portfolio_id}.log"
        self.assertTrue(os.path.exists(expected_log_path))

        with open(expected_log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(rand_portfolio_id, log_content)
            self.assertIn(str(rand_liquidity), log_content)

        mock_db_func.assert_called_once()
        called_arg = mock_db_func.call_args[0][0]
        self.assertEqual(called_arg.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(called_arg.get("target_liquidity"), rand_liquidity)
        self.assertEqual(called_arg.get("status"), "tracked")

        if os.path.exists(expected_log_path):
            os.remove(expected_log_path)

if __name__ == "__main__":
    unittest.main()