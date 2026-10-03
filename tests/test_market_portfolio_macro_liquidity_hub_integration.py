import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_hub import market_portfolio_macro_liquidity_hub
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioMacroLiquidityHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_portfolio_id = str(uuid.uuid4())
        self.random_liquidity_factor = round(random.uniform(0.1, 5.0), 4)
        self.random_volume = random.randint(10000, 1000000)
        self.db_path = "test_market_liquidity.db"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_macro_liquidity_hub_end_to_end(self):
        db_instance = db_storage(db_path=self.db_path)
        collector_instance = market_portfolio_collector_agent(db=db_instance)

        raw_data = {
            "portfolio_id": self.test_portfolio_id,
            "liquidity_factor": self.random_liquidity_factor,
            "aggregate_volume": self.random_volume,
            "metric_type": "macro_liquidity"
        }

        ingested_record = collector_instance.collect(raw_data)
        self.assertIsNotNone(ingested_record)

        hub_instance = market_portfolio_macro_liquidity_hub(db=db_instance)
        aggregated_result = hub_instance.aggregate_and_sync(portfolio_id=self.test_portfolio_id)

        self.assertIsInstance(aggregated_result, dict)
        self.assertIn("status", aggregated_result)
        self.assertEqual(aggregated_result.get("portfolio_id"), self.test_portfolio_id)
        self.assertEqual(aggregated_result.get("liquidity_factor"), self.random_liquidity_factor)

        persisted_data = db_instance.get_record(self.test_portfolio_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data["aggregate_volume"], self.random_volume)

if __name__ == "__main__":
    unittest.main()