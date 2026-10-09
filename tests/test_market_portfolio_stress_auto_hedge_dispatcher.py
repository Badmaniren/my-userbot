import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import sqlite3

from skills.market_portfolio_stress_auto_hedge_dispatcher import (
    MarketPortfolioStressAutoHedgeDispatcher,
    AutoHedgeDispatcherError
)

class TestMarketPortfolioStressAutoHedgeDispatcher(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.db_path = f"test_{uuid.uuid4().hex[:8]}.db"

        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()
        self.mock_advisor = MagicMock()
        self.mock_pipeline = MagicMock()

        self.dispatcher = MarketPortfolioStressAutoHedgeDispatcher(
            db_storage=self.db_path,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )

    def tearDown(self):
        import os
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_dispatch_auto_hedge_stable(self):
        self.mock_advisor.analyze_and_recommend.return_value = {
            "status": "STABLE",
            "reason": "No stress trigger activated"
        }

        result = self.dispatcher.dispatch_auto_hedge(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )

        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.mock_pipeline.run_stress_execution.assert_not_called()

    def test_dispatch_auto_hedge_triggered(self):
        ticker = f"TICK_{random.choice(['AAPL', 'TSLA', 'MSFT', 'GOOG'])}"
        volume = random.randint(10, 500)
        shift = float(random.choice([-0.05, -0.1, -0.2]))

        self.mock_advisor.analyze_and_recommend.return_value = {
            "status": "STRESS",
            "ticker": ticker,
            "volume": volume,
            "shifts": [shift]
        }

        pipeline_res = {"status": "EXECUTED", "order_id": uuid.uuid4().hex[:6]}
        self.mock_pipeline.run_stress_execution.return_value = pipeline_res

        result = self.dispatcher.dispatch_auto_hedge(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["execution_result"], pipeline_res)
        self.mock_pipeline.run_stress_execution.assert_called_once_with(
            symbol=ticker,
            volume=volume,
            shifts=[shift]
        )

    def test_dispatch_auto_hedge_with_market_context(self):
        ticker = f"CTX_{random.choice(['SPY', 'QQQ', 'BTC'])}"
        volume = random.randint(50, 1000)
        shift = float(random.choice([-0.15, -0.25]))

        market_context = {
            "ticker": ticker,
            "volume": volume,
            "shift": shift
        }

        self.mock_advisor.analyze_and_recommend.return_value = {
            "status": "STRESS",
            "ticker": ticker,
            "volume": volume,
            "shifts": [shift]
        }

        pipeline_res = {"status": "CONTEXT_EXECUTED", "id": uuid.uuid4().hex[:6]}
        self.mock_pipeline.run_stress_execution.return_value = pipeline_res

        result = self.dispatcher.dispatch_auto_hedge(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            market_context=market_context
        )

        self.assertEqual(result["dispatch_status"], "SUCCESS")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["execution_results"], pipeline_res)
        self.mock_pipeline.run_stress_execution.assert_called_once_with(
            symbol=ticker,
            volume=volume,
            shifts=[shift]
        )

    def test_dispatch_batch(self):
        p_ids = [f"port_{uuid.uuid4().hex[:4]}" for _ in range(3)]
        r_ids = [f"req_{uuid.uuid4().hex[:4]}" for _ in range(3)]

        self.mock_advisor.analyze_and_recommend.return_value = {
            "status": "STABLE",
            "reason": "Stable state"
        }

        results = self.dispatcher.dispatch_batch(portfolio_ids=p_ids, request_ids=r_ids)

        self.assertEqual(len(results), 3)
        for idx, res in enumerate(results):
            self.assertEqual(res["portfolio_id"], p_ids[idx])
            self.assertEqual(res["status"], "SKIPPED")

    def test_dispatch_auto_hedge_raises_dispatcher_error(self):
        err_msg = f"Critical failure {uuid.uuid4().hex[:6]}"
        self.mock_advisor.analyze_and_recommend.side_effect = Exception(err_msg)

        with self.assertRaises(AutoHedgeDispatcherError) as ctx:
            self.dispatcher.dispatch_auto_hedge(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id
            )

        self.assertIn(err_msg, str(ctx.exception))

    def test_auto_hedge_dispatcher_error_preservation(self):
        err_msg = f"Specific dispatcher error {uuid.uuid4().hex[:6]}"
        self.mock_advisor.analyze_and_recommend.side_effect = AutoHedgeDispatcherError(err_msg)

        with self.assertRaises(AutoHedgeDispatcherError) as ctx:
            self.dispatcher.dispatch_auto_hedge(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id
            )

        self.assertEqual(str(ctx.exception), err_msg)