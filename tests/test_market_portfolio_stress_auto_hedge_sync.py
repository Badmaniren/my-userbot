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
        self.shifts = [random.randint(-10, 10) for _ in range(3)]

    def test_dummy_monitor(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(state["portfolio_id"], self.portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": ''.join(random.choices(string.ascii_lowercase, k=8))}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], status_data)

    def test_auto_hedge_sync_initialization_defaults(self):
        sync_inst = MarketPortfolioStressAutoHedgeSync()
        self.assertIsInstance(sync_inst.monitor, DummyMonitor)
        self.assertIsInstance(sync_inst.rebalancer, DummyRebalancer)
        self.assertIsNotNone(sync_inst.advisor)
        self.assertIsNotNone(sync_inst.pipeline)
        self.assertIsNone(sync_inst.stream_handler)

    def test_synchronize_execution(self):
        mock_advisor = MagicMock()
        expected_advisor_result = {"recommendation_id": str(uuid.uuid4()), "action": "hedge"}
        mock_advisor.analyze_and_recommend.return_value = expected_advisor_result

        mock_pipeline = MagicMock()
        expected_pipeline_result = {"pipeline_id": str(uuid.uuid4()), "status": "completed"}
        mock_pipeline.execute.return_value = expected_pipeline_result

        sync_inst = MarketPortfolioStressAutoHedgeSync(
            advisor=mock_advisor,
            pipeline=mock_pipeline
        )

        result = sync_inst.synchronize(
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
        self.assertEqual(result["advisor_recommendation"], expected_advisor_result)
        self.assertEqual(result["stress_pipeline_result"], expected_pipeline_result)

    def test_synchronize_resets_missing_advisor_dependencies(self):
        mock_advisor = MagicMock()
        mock_advisor.monitor = None
        mock_advisor.rebalancer = None

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"status": "ok"}

        custom_monitor = DummyMonitor()
        custom_rebalancer = DummyRebalancer()

        sync_inst = MarketPortfolioStressAutoHedgeSync(
            monitor=custom_monitor,
            rebalancer=custom_rebalancer,
            advisor=mock_advisor,
            pipeline=mock_pipeline
        )

        sync_inst.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(mock_advisor.monitor, custom_monitor)
        self.assertEqual(mock_advisor.rebalancer, custom_rebalancer)

    def test_run_auto_hedge_sync_helper(self):
        db_storage = MagicMock()
        monitor = MagicMock()
        evaluator = MagicMock()
        rebalancer = MagicMock()
        storage_file = str(uuid.uuid4()) + ".json"

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncClass:
            mock_instance = MockSyncClass.return_value
            expected_return = {"status": "success", "id": str(uuid.uuid4())}
            mock_instance.synchronize.return_value = expected_return

            res = run_auto_hedge_sync(
                db_storage=db_storage,
                monitor=monitor,
                evaluator=evaluator,
                rebalancer=rebalancer,
                storage_file=storage_file,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            MockSyncClass.assert_called_once_with(
                db_storage=db_storage,
                monitor=monitor,
                evaluator=evaluator,
                rebalancer=rebalancer,
                storage_file=storage_file
            )
            mock_instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_return)


if __name__ == "__main__":
    unittest.main()