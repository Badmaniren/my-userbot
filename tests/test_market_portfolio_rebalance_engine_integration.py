import unittest
import uuid
import os
import random
from skills.db_storage import db_storage
from skills.market_portfolio_rebalance_engine import market_portfolio_rebalance_engine


class TestMarketPortfolioRebalanceEngineIntegration(unittest.TestCase):

    def test_execute_rebalance_integration(self):
        portfolio_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        initial_assets = {"ETH": round(random.uniform(1.0, 10.0), 4)}
        db_storage.save_portfolio({
            "portfolio_id": portfolio_id,
            "assets": initial_assets
        })

        config = {
            "portfolio_id": portfolio_id,
            "job_id": job_id
        }

        result = market_portfolio_rebalance_engine.execute_rebalance(config)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["job_id"], job_id)
        self.assertIn("executed_trades", result)
        self.assertGreater(len(result["executed_trades"]), 0)

        updated_portfolio = db_storage.get_portfolio(portfolio_id)
        self.assertIsNotNone(updated_portfolio)
        self.assertIn("last_rebalance_timestamp", updated_portfolio)
        self.assertIsInstance(updated_portfolio["last_rebalance_timestamp"], float)

        export_path = f"./audit_logs/rebalance_{portfolio_id}.json"
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("AUDIT_LOG", content)

        if os.path.exists(export_path):
            os.remove(export_path)


if __name__ == "__main__":
    unittest.main()