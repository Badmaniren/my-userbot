import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"stress_pipeline_{uuid.uuid4()}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_synchronize_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        symbols = ["AAPL", "BTC", "ETH", "TSLA", "SPY"]
        symbol = random.choice(symbols)
        percentage = round(random.uniform(5.0, 35.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        result = syncer.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("request_id"), request_id)

        advisor_recommendation = result.get("advisor_recommendation")
        self.assertIsNotNone(advisor_recommendation)

        stress_pipeline_result = result.get("stress_pipeline_result")
        self.assertIsNotNone(stress_pipeline_result)

    def test_run_auto_hedge_sync_wrapper(self):
        portfolio_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        symbol = "MSFT"
        percentage = 15.5
        shifts = [0.01, -0.02, 0.03]

        result = run_auto_hedge_sync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file,
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["request_id"], request_id)
        self.assertIn("advisor_recommendation", result)
        self.assertIn("stress_pipeline_result", result)


if __name__ == "__main__":
    unittest.main()