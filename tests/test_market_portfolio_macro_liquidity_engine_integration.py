import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_macro_liquidity_engine import (
    db_storage,
    market_portfolio_collector_agent,
    market_portfolio_liquidity_scenario_analyzer,
    market_portfolio_macro_liquidity_engine
)

class TestMarketPortfolioMacroLiquidityEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.test_asset = f"ASSET_{random.choice(['BTC', 'ETH', 'SOL', 'USDT'])}"
        self.test_liquidity_factor = round(random.uniform(0.1, 9.9), 4)
        
        self.db = db_storage()
        self.collector = market_portfolio_collector_agent()
        self.scenario_analyzer = market_portfolio_liquidity_scenario_analyzer()
        self.engine = market_portfolio_macro_liquidity_engine()

    def test_macro_liquidity_pipeline_integration(self):
        raw_market_data = {
            "portfolio_id": self.test_portfolio_id,
            "asset": self.test_asset,
            "liquidity_index": self.test_liquidity_factor,
            "timestamp": uuid.uuid1().int
        }

        ingested_data = self.collector.collect(raw_market_data)
        self.assertIsNotNone(ingested_data)

        db_save_status = self.db.persist(self.test_portfolio_id, ingested_data)
        self.assertTrue(db_save_status)

        scenario_result = self.scenario_analyzer.evaluate(self.test_portfolio_id, {
            "stress_multiplier": random.choice([1.5, 2.0, 3.5])
        })
        self.assertIn("status", scenario_result)

        engine_report = self.engine.analyze_macro_liquidity(self.test_portfolio_id)
        
        self.assertIsInstance(engine_report, dict)
        self.assertIn("macro_score", engine_report)
        self.assertEqual(engine_report.get("target_portfolio"), self.test_portfolio_id)

    def tearDown(self):
        if hasattr(self.db, "cleanup"):
            self.db.cleanup(self.test_portfolio_id)

if __name__ == "__main__":
    unittest.main()