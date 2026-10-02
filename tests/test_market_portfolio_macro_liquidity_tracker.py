import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
import os

from skills.market_portfolio_macro_liquidity_tracker import start_new, market_portfolio_macro_liquidity_tracker

class TestMarketPortfolioMacroLiquiditytracker(unittest.TestCase):

    def test_start_new_with_db(self):
        db_mock = MagicMock()
        rand_key = uuid.uuid4().hex

        result = start_new(db_storage=db_mock)

        db_mock.connect.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_start_new_with_parser(self):
        parser_mock = MagicMock()
        parsed_value = uuid.uuid4().hex
        parser_mock.parse_stream.return_value = parsed_value

        result = start_new(market_parser=parser_mock)

        parser_mock.parse_stream.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_start_new_with_collector_agent(self):
        collector_mock = MagicMock()
        expected_macro = {uuid.uuid4().hex: random.random()}
        collector_mock.fetch_macro_data.return_value = expected_macro

        result = start_new(market_portfolio_collector_agent=collector_mock)

        collector_mock.fetch_macro_data.assert_called_once()
        self.assertEqual(result, expected_macro)

    def test_start_new_default(self):
        result = start_new()
        self.assertEqual(result, {"status": "success"})

    def test_market_portfolio_macro_liquidity_tracker_execution(self):
        portfolio_id = uuid.uuid4().hex
        output_target = f"{uuid.uuid4().hex}.json"
        macro_indicators = {uuid.uuid4().hex: random.randint(100, 999)}
        var_core_metrics = {uuid.uuid4().hex: random.uniform(0.1, 0.9)}

        payload = {
            "portfolio_id": portfolio_id,
            "output_target": output_target,
            "macro_indicators": macro_indicators,
            "var_core_metrics": var_core_metrics
        }

        with patch("skills.market_portfolio_macro_liquidity_tracker.db_storage") as mock_db_storage:
            try:
                response = market_portfolio_macro_liquidity_tracker(payload)

                self.assertEqual(response["portfolio_id"], portfolio_id)
                self.assertTrue(response["success"])
                self.assertEqual(response["macro_data"], macro_indicators)
                self.assertEqual(response["var_metrics"], var_core_metrics)

                self.assertTrue(os.path.exists(output_target))
                with open(output_target, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    self.assertEqual(file_data["portfolio_id"], portfolio_id)
                    self.assertEqual(file_data["macro_data"], macro_indicators)

                mock_db_storage.assert_called_once_with({
                    "action": "set",
                    "key": portfolio_id,
                    "value": response
                })
            finally:
                if os.path.exists(output_target):
                    os.remove(output_target)

if __name__ == "__main__":
    unittest.main()