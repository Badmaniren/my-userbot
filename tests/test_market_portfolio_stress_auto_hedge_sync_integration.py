import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"stress_storage_{uuid.uuid4()}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_auto_hedge_sync_integration(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        request_id = f"req-{uuid.uuid4()}"
        symbol = random.choice(["BTC", "ETH", "AAPL", "TSLA", "SPY"])
        percentage = round(random.uniform(0.01, 0.5), 4)
        shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(3)]

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

        advisor_rec = result.get("advisor_recommendation")
        self.assertIsNotNone(advisor_rec)
        self.assertIsInstance(advisor_rec, dict)

        pipeline_res = result.get("stress_pipeline_result")
        self.assertIsNotNone(pipeline_res)
        self.assertIsInstance(pipeline_res, dict)

        portfolio_id_alt = f"port-{uuid.uuid4()}"
        request_id_alt = f"req-{uuid.uuid4()}"
        symbol_alt = random.choice(["MSFT", "GOOGL", "AMZN"])
        percentage_alt = round(random.uniform(0.05, 0.3), 4)
        shifts_alt = [round(random.uniform(-0.1, 0.1), 4) for _ in range(2)]

        func_result = run_auto_hedge_sync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file,
            portfolio_id=portfolio_id_alt,
            request_id=request_id_alt,
            symbol=symbol_alt,
            percentage=percentage_alt,
            shifts=shifts_alt
        )

        self.assertIsInstance(func_result, dict)
        self.assertEqual(func_result.get("status"), "success")
        self.assertEqual(func_result.get("portfolio_id"), portfolio_id_alt)
        self.assertEqual(func_result.get("request_id"), request_id_alt)


if __name__ == "__main__":
    unittest.main()