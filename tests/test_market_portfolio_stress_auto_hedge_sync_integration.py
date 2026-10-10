import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = "TEST_" + str(uuid.uuid4())[:6].upper()
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4), round(random.uniform(-0.2, 0.2), 4)]
        self.storage_file = f"test_stress_pipeline_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_synchronization_integration_flow(self):
        advisor = MarketPortfolioStressHedgeAdvisor()
        pipeline = PortfolioStressScenarioPipeline(storage_file=self.storage_file)
        
        sync_module = MarketPortfolioStressAutoHedgeSync(
            advisor=advisor,
            pipeline=pipeline,
            storage_file=self.storage_file
        )

        result = sync_module.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)

        advisor_rec = result.get("advisor_recommendation")
        self.assertIsInstance(advisor_rec, dict)
        self.assertEqual(advisor_rec.get("portfolio_id"), self.portfolio_id)

        stress_res = result.get("stress_pipeline_result")
        self.assertIsInstance(stress_res, dict)

        self.assertTrue(os.path.exists(self.storage_file))

    def test_synchronization_invalid_percentage(self):
        invalid_percentage = 150.0
        sync_module = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        result = sync_module.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=invalid_percentage,
            shifts=self.shifts
        )

        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        self.assertIn("percentage", result.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()