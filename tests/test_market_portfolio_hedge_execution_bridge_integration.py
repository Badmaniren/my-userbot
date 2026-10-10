import unittest
import os
import uuid
import random
from skills.market_portfolio_hedge_execution_bridge import (
    MarketPortfolioHedgeExecutionBridge
)
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    DummyMonitor,
    DummyRebalancer
)
from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline
)

class TestMarketPortfolioHedgeExecutionBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["AAPL", "TSLA", "BTC", "ETH", "SPY"])
        self.percentage = round(random.uniform(0.01, 0.25), 4)
        self.shifts = [round(random.uniform(-0.1, -0.01), 4) for _ in range(3)]
        
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.pipeline_storage = f"test_pipeline_{uuid.uuid4().hex}.json"
        
        self.monitor = DummyMonitor()
        self.rebalancer = DummyRebalancer()
        self.pipeline = MarketPortfolioExecutionPipeline(storage_file=self.pipeline_storage)
        
        self.auto_hedge_sync = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.storage_file,
            monitor=self.monitor,
            evaluator=None,
            rebalancer=self.rebalancer,
            storage_file=self.storage_file,
            advisor=None,
            pipeline=self.pipeline
        )
        
        self.bridge = MarketPortfolioHedgeExecutionBridge(
            auto_hedge_sync=self.auto_hedge_sync,
            execution_pipeline=self.pipeline,
            storage_file=self.storage_file
        )

    def tearDown(self):
        for f in [self.storage_file, self.pipeline_storage]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_hedge_execution_bridge_integration(self):
        result = self.bridge.execute_hedge_protection(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("execution_details", result)
        
        self.assertTrue(
            os.path.exists(self.storage_file),
            "Модуль обязан сохранять состояние в db_storage/storage_file"
        )
        
        logs = self.pipeline.get_historical_pipeline_logs(self.request_id)
        self.assertIsInstance(logs, list)

if __name__ == "__main__":
    unittest.main()