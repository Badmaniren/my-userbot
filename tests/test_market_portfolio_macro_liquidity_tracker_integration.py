import unittest
import os
import uuid
import random

from skills.market_portfolio_macro_liquidity_tracker import market_portfolio_macro_liquidity_tracker, start_new
from skills.db_storage import db_storage

class TestMarketPortfolioMacroLiquidityTrackerIntegration(unittest.TestCase):

    def test_macro_liquidity_tracker_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        target_liquidity = round(random.uniform(1000.0, 500000.0), 2)
        
        tracker_input = {
            "portfolio_id": portfolio_id,
            "target_liquidity": target_liquidity
        }

        result = market_portfolio_macro_liquidity_tracker(tracker_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("liquidity"), target_liquidity)

        log_file_path = f"logs/macro_liquidity_{portfolio_id}.log"
        self.assertTrue(os.path.exists(log_file_path), "Интеграционный тест требует создания реального лог-файла на диске.")
        
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(portfolio_id, log_content)
            self.assertIn(str(target_liquidity), log_content)

        db_payload = {
            "action": "fetch",
            "portfolio_id": portfolio_id
        }
        db_storage(db_payload)

    def test_start_new_with_real_dependencies(self):
        class DummyDB:
            def fetch_macro_data(self):
                return {"macro_status": "active_real_data", "rnd": random.randint(1, 100)}

        dependencies = {
            "db_storage": DummyDB()
        }

        res = start_new(dependencies)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("macro_status"), "active_real_data")

if __name__ == "__main__":
    unittest.main()