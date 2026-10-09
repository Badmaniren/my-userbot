import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_auto_hedge_executor import (
    MarketPortfolioStressAutoHedgeExecutor
)
from skills.market_portfolio_stress_hedge_advisor import (
    MarketPortfolioStressHedgeAdvisor
)
from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline
)


class TestMarketPortfolioStressAutoHedgeExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        self.pipeline = MarketPortfolioExecutionPipeline(storage_file=self.db_path)
        self.advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=self.db_path,
            monitor=None,
            evaluator=None,
            rebalancer=None
        )
        self.executor = MarketPortfolioStressAutoHedgeExecutor(
            hedge_advisor=self.advisor,
            execution_pipeline=self.pipeline
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_auto_hedge_execution_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        selected_ticker = random.choice(tickers)
        volume = random.randint(10, 500)
        shifts = [random.uniform(-0.15, -0.01), random.uniform(-0.25, -0.05)]

        market_context = {
            "volatility": random.uniform(0.1, 0.5),
            "trend": "bearish",
            "liquidity_index": random.uniform(0.5, 1.0)
        }

        result = self.executor.execute_stress_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id,
            ticker=selected_ticker,
            volume=volume,
            shifts=shifts,
            market_context=market_context
        )

        self.assertIsInstance(result, dict)
        self.assertIn("execution_status", result)
        self.assertIn("recommendation_id", result)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("request_id"), request_id)

        history = self.pipeline.get_historical_pipeline_logs(selected_ticker)
        self.assertIsInstance(history, list)


if __name__ == "__main__":
    unittest.main()