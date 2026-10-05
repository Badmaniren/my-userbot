import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_tracker import market_portfolio_macro_liquidity_tracker, MarketPortfolioMacroLiquidityTracker
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub

class TestMarketPortfolioMacroLiquidityTrackerIntegration(unittest.TestCase):
    def test_macro_liquidity_tracker_integration(self):
        unique_id = str(uuid.uuid4())
        random_metric = round(random.uniform(1.0, 100.0), 2)
        export_filename = f"test_export_{unique_id}.txt"

        payload = {
            "id": unique_id,
            "liquidity_metric": random_metric,
            "export_target": export_filename
        }

        try:
            result = market_portfolio_macro_liquidity_tracker(payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("processed_id"), unique_id)

            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r") as f:
                content = f.read()
                self.assertEqual(content, str(random_metric))

            tracker = MarketPortfolioMacroLiquidityTracker(db_storage=db_storage)
            self.assertIsNotNone(tracker)

        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

if __name__ == "__main__":
    unittest.main()