import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_auto_hedge_dispatcher import MarketPortfolioStressAutoHedgeDispatcher, AutoHedgeDispatcherError

class TestMarketPortfolioStressAutoHedgeDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.db_filename = f"test_storage_{uuid.uuid4()}.db"
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"

        tickers = ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN"]
        self.market_context = {
            "ticker": random.choice(tickers),
            "volume": random.randint(10, 500),
            "shift": round(random.uniform(-0.2, -0.05), 2)
        }

        self.dispatcher = MarketPortfolioStressAutoHedgeDispatcher(db_storage=self.db_filename)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except OSError:
                pass

    def test_dispatch_auto_hedge_integration_success(self):
        result = self.dispatcher.dispatch_auto_hedge(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            market_context=self.market_context
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("dispatch_status"), "SUCCESS")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)

        execution_results = result.get("execution_results")
        self.assertIsNotNone(execution_results)

        recommendation = result.get("recommendation")
        self.assertIsInstance(recommendation, dict)

    def test_dispatch_batch_integration(self):
        portfolio_ids = [f"port_{uuid.uuid4().hex[:6]}" for _ in range(2)]
        request_ids = [f"req_{uuid.uuid4().hex[:6]}" for _ in range(2)]

        results = self.dispatcher.dispatch_batch(portfolio_ids, request_ids)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

        for res, pid, rid in zip(results, portfolio_ids, request_ids):
            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("portfolio_id"), pid)
            self.assertEqual(res.get("request_id"), rid)

    def test_dispatcher_error_handling(self):
        # Передаем некорректный тип данных через context для вызова исключения
        invalid_context = "not_a_dict"
        with self.assertRaises(AutoHedgeDispatcherError):
            self.dispatcher.dispatch_auto_hedge(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                market_context=invalid_context
            )

if __name__ == "__main__":
    unittest.main()