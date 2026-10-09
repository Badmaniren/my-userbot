import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    run_auto_hedge_sync,
    DummyMonitor,
    DummyRebalancer
)


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(2, 5))]
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(state["portfolio_id"], self.portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": ''.join(random.choices(string.ascii_lowercase, k=8))}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], status_data)

    def test_auto_hedge_sync_initialization_defaults(self):
        sync_instance = MarketPortfolioStressAutoHedgeSync(storage_file=self.storage_file)
        self.assertIsInstance(sync_instance.monitor, DummyMonitor)
        self.assertIsInstance(sync_instance.rebalancer, DummyRebalancer)
        self.assertIsNotNone(sync_instance.advisor)
        self.assertIsNotNone(sync_instance.pipeline)

    def test_synchronize_execution_flow(self):
        mock_db = MagicMock()
        mock_evaluator = MagicMock()
        mock_advisor = MagicMock()
        expected_recommendation = {
            "recommendation_id": str(uuid.uuid4()),
            "action": random.choice(["HEDGE", "HOLD", "LIQUIDATE"])
        }
        mock_advisor.analyze_and_recommend.return_value = expected_recommendation

        mock_pipeline = MagicMock()
        expected_pipeline_result = {
            "pipeline_status": "executed",
            "symbol": self.symbol,
            "impact": random.randint(100, 5000)
        }
        mock_pipeline.execute.return_value = expected_pipeline_result

        sync_instance = MarketPortfolioStressAutoHedgeSync(
            db_storage=mock_db,
            evaluator=mock_evaluator,
            advisor=mock_advisor,
            pipeline=mock_pipeline,
            storage_file=self.storage_file
        )

        result = sync_instance.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["advisor_recommendation"], expected_recommendation)
        self.assertEqual(result["stress_pipeline_result"], expected_pipeline_result)

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_run_auto_hedge_sync_wrapper(self):
        mock_db = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        mock_rebalancer = MagicMock()

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as mock_sync_cls:
            mock_instance = mock_sync_cls.return_value
            expected_payload = {
                "status": "success",
                "portfolio_id": self.portfolio_id,
                "request_id": self.request_id,
                "advisor_recommendation": {},
                "stress_pipeline_result": {}
            }
            mock_instance.synchronize.return_value = expected_payload

            response = run_auto_hedge_sync(
                db_storage=mock_db,
                monitor=mock_monitor,
                evaluator=mock_evaluator,
                rebalancer=mock_rebalancer,
                storage_file=self.storage_file,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_sync_cls.assert_called_once_with(
                db_storage=mock_db,
                monitor=mock_monitor,
                evaluator=mock_evaluator,
                rebalancer=mock_rebalancer,
                storage_file=self.storage_file
            )
            mock_instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(response, expected_payload)


if __name__ == "__main__":
    unittest.main()