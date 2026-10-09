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
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [random.randint(-10, 10) for _ in range(3)]
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(state["portfolio_id"], self.portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": "".join(random.choices(string.ascii_lowercase, k=6))}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], status_data)

    def test_auto_hedge_sync_initialization_defaults(self):
        syncer = MarketPortfolioStressAutoHedgeSync(storage_file=self.storage_file)
        self.assertIsInstance(syncer.monitor, DummyMonitor)
        self.assertIsInstance(syncer.rebalancer, DummyRebalancer)
        self.assertIsNotNone(syncer.advisor)
        self.assertIsNotNone(syncer.pipeline)

    def test_synchronize_execution_flow(self):
        mock_advisor = MagicMock()
        expected_recommendation = {
            "rec_id": str(uuid.uuid4()),
            "action": "".join(random.choices(string.ascii_lowercase, k=4))
        }
        mock_advisor.analyze_and_recommend.return_value = expected_recommendation

        mock_pipeline = MagicMock()
        expected_pipeline_res = {
            "pipeline_id": str(uuid.uuid4()),
            "metric": random.randint(100, 999)
        }
        mock_pipeline.execute.return_value = expected_pipeline_res

        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=mock_advisor,
            pipeline=mock_pipeline,
            storage_file=self.storage_file
        )

        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )

        mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["advisor_recommendation"], expected_recommendation)
        self.assertEqual(result["stress_pipeline_result"], expected_pipeline_res)

    def test_run_auto_hedge_sync_wrapper(self):
        db_storage_mock = MagicMock()
        monitor_mock = MagicMock()
        evaluator_mock = MagicMock()
        rebalancer_mock = MagicMock()

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as mock_cls:
            mock_instance = mock_cls.return_value
            expected_output = {
                "status": "success",
                "random_key": str(uuid.uuid4())
            }
            mock_instance.synchronize.return_value = expected_output

            res = run_auto_hedge_sync(
                db_storage=db_storage_mock,
                monitor=monitor_mock,
                evaluator=evaluator_mock,
                rebalancer=rebalancer_mock,
                storage_file=self.storage_file,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_cls.assert_called_once_with(
                db_storage=db_storage_mock,
                monitor=monitor_mock,
                evaluator=evaluator_mock,
                rebalancer=rebalancer_mock,
                storage_file=self.storage_file
            )

            mock_instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res, expected_output)


if __name__ == "__main__":
    unittest.main()