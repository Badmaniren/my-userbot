import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class RealMonitor:
    def get_portfolio_state(self, portfolio_id):
        return {"portfolio_id": portfolio_id, "status": "active", "checked": True}


class RealRebalancer:
    def set_trigger_status(self, portfolio_id, status_data):
        return {"portfolio_id": portfolio_id, "status": "synced", "data": status_data}


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.request_id = f"req-{uuid.uuid4()}"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4), round(random.uniform(-0.2, 0.2), 4)]
        self.storage_file = f"test_stress_storage_{uuid.uuid4()}.json"

        self.monitor = RealMonitor()
        self.rebalancer = RealRebalancer()
        
        self.advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=None,
            monitor=self.monitor,
            evaluator=None,
            rebalancer=self.rebalancer
        )
        
        self.pipeline = PortfolioStressScenarioPipeline(
            storage_file=self.storage_file
        )

        self.sync_module = MarketPortfolioStressAutoHedgeSync(
            db_storage=None,
            monitor=self.monitor,
            evaluator=None,
            rebalancer=self.rebalancer,
            storage_file=self.storage_file,
            advisor=self.advisor,
            pipeline=self.pipeline
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_synchronize_integration_success(self):
        result = self.sync_module.synchronize(
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

    def test_synchronize_invalid_percentage(self):
        invalid_percentage = random.choice([-10.0, 0, 105.0])
        result = self.sync_module.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=invalid_percentage,
            shifts=self.shifts
        )

        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        self.assertIn("percentage", result.get("error").lower())

    def test_synchronize_invalid_shifts(self):
        invalid_shifts = "not-a-list"
        result = self.sync_module.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=invalid_shifts
        )

        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        self.assertIn("shifts", result.get("error").lower())


if __name__ == "__main__":
    unittest.main()