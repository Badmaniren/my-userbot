import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_hedge_order_router import MarketPortfolioHedgeOrderRouter

class IntegrationTestMarketPortfolioHedgeOrderRouter(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "BTC_USD"])
        self.percentage = round(random.uniform(1.0, 15.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.storage_file = f"test_execution_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_hedge_order_router_integration_real_skills(self):
        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)

        class RealMonitor:
            def get_portfolio_state(self, portfolio_id):
                return {"portfolio_id": portfolio_id, "status": "active", "balance": 100000.0}

        class RealRebalancer:
            def set_trigger_status(self, portfolio_id, status_data):
                return {"portfolio_id": portfolio_id, "status_data": status_data, "updated": True}

        monitor = RealMonitor()
        rebalancer = RealRebalancer()

        sync_module = MarketPortfolioStressAutoHedgeSync(
            db_storage=None,
            monitor=monitor,
            evaluator=None,
            rebalancer=rebalancer,
            storage_file=self.storage_file,
            advisor=None,
            pipeline=pipeline
        )

        router = MarketPortfolioHedgeOrderRouter(
            stress_sync_module=sync_module,
            execution_pipeline=pipeline
        )

        self.assertTrue(hasattr(router, "route_hedge_signal"), "Модуль должен иметь метод route_hedge_signal")

        route_result = router.route_hedge_signal(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(route_result, dict, "Результат маршрутизации должен быть словарем")
        self.assertIn("execution_result", route_result)
        self.assertIn("sync_status", route_result)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища пайплайна должен быть создан в процессе выполнения")

        logs = pipeline.get_historical_pipeline_logs(self.request_id)
        self.assertIsInstance(logs, list)

if __name__ == "__main__":
    unittest.main()