import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def test_auto_hedge_sync_integration(self):
        portfolio_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        symbol = f"SYM_{random.randint(100, 999)}"
        percentage = round(random.uniform(1.0, 20.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4), round(random.uniform(-0.1, 0.1), 4)]
        storage_file = f"test_stress_pipeline_{uuid.uuid4()}.json"

        try:
            result = run_auto_hedge_sync(
                db_storage=None,
                monitor=None,
                evaluator=None,
                rebalancer=None,
                storage_file=storage_file,
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

            stress_res = result.get("stress_pipeline_result")
            self.assertIsNotNone(stress_res)
            self.assertIsInstance(stress_res, dict)

        finally:
            if os.path.exists(storage_file):
                try:
                    os.remove(storage_file)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()