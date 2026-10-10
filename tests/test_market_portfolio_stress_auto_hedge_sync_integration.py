import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = f"TEST_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.storage_file = f"test_stress_pipeline_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_real_integration_synchronize(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )
        
        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        
        advisor_rec = result.get("advisor_recommendation", {})
        self.assertIsInstance(advisor_rec, dict)
        self.assertEqual(advisor_rec.get("portfolio_id"), self.portfolio_id)

        stress_res = result.get("stress_pipeline_result")
        self.assertIsNotNone(stress_res)

    def test_real_integration_run_auto_hedge_sync(self):
        result = run_auto_hedge_sync(
            db_storage=None,
            monitor=None,
            evaluator=None,
            rebalancer=None,
            storage_file=self.storage_file,
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        self.assertIn("advisor_recommendation", result)
        self.assertIn("stress_pipeline_result", result)


if __name__ == "__main__":
    unittest.main()