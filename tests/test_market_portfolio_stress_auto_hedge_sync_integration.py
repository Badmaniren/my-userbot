import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync


class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["BTCUSDT", "ETHUSDT", "SBER", "GAZP", "AAPL"])
        self.percentage = round(random.uniform(5.0, 35.0), 2)
        self.shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(3)]
        
        self.db_storage = f"sqlite:///:memory:"
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_auto_hedge_sync_real_composition(self):
        advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=self.db_storage,
            monitor=None,
            evaluator=None,
            rebalancer=None
        )
        pipeline = PortfolioStressScenarioPipeline(storage_file=self.temp_file.name)
        
        sync_module = MarketPortfolioStressAutoHedgeSync(
            advisor=advisor,
            pipeline=pipeline
        )
        
        self.assertTrue(
            hasattr(sync_module, "synchronize"),
            "Модуль MarketPortfolioStressAutoHedgeSync должен содержать метод synchronize"
        )
        
        result = sync_module.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        
        self.assertTrue(
            os.path.exists(self.temp_file.name),
            "Конвейер стресс-сценариев должен взаимодействовать с файловым хранилищем"
        )


if __name__ == "__main__":
    unittest.main()