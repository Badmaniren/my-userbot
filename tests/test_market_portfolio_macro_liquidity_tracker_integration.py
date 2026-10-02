import unittest
import uuid
import os
import json
from skills.market_portfolio_macro_liquidity_tracker import market_portfolio_macro_liquidity_tracker
from skills.db_storage import db_storage

class TestMarketPortfolioMacroLiquiditytrackerIntegration(unittest.TestCase):
    def test_macro_liquidity_tracker_integration(self):
        portfolio_id = str(uuid.uuid4())
        output_target = f"test_macro_output_{uuid.uuid4()}.json"

        macro_indicators = {
            "interest_rate": 5.25,
            "liquidity_index": round(uuid.uuid4().int % 1000 / 10.0, 2)
        }
        var_core_metrics = {
            "var_95": round(uuid.uuid4().int % 10000 / 100.0, 2)
        }

        payload = {
            "portfolio_id": portfolio_id,
            "output_target": output_target,
            "macro_indicators": macro_indicators,
            "var_core_metrics": var_core_metrics
        }

        try:
            response = market_portfolio_macro_liquidity_tracker(payload)

            self.assertEqual(response.get("portfolio_id"), portfolio_id)
            self.assertTrue(response.get("success"))
            self.assertEqual(response.get("macro_data"), macro_indicators)
            self.assertEqual(response.get("var_metrics"), var_core_metrics)

            self.assertTrue(os.path.exists(output_target))
            with open(output_target, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            self.assertEqual(file_data.get("portfolio_id"), portfolio_id)
            self.assertEqual(file_data.get("macro_data"), macro_indicators)

            stored_value = db_storage({"action": "get", "key": portfolio_id})
            self.assertEqual(stored_value.get("portfolio_id"), portfolio_id)
            self.assertEqual(stored_value.get("macro_data"), macro_indicators)

        finally:
            if os.path.exists(output_target):
                os.remove(output_target)

if __name__ == "__main__":
    unittest.main()