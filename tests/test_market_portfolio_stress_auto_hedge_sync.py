import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.market_portfolio_stress_auto_hedge_sync import (
    DummyMonitor,
    DummyRebalancer,
    MarketPortfolioStressAutoHedgeSync,
    run_auto_hedge_sync
)


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 99.9), 2)
        self.shifts = random.randint(1, 10)

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(state["portfolio_id"], self.portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        data = {"action": uuid.uuid4().hex}
        res = rebalancer.set_trigger_status(self.portfolio_id, data)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], data)

    def test_synchronize_execution_flow(self):
        mock_advisor = MagicMock()
        expected_recommendation = {"action": uuid.uuid4().hex, "volume": random.randint(10, 1000)}
        mock_advisor.analyze_and_recommend.return_value = expected_recommendation

        mock_pipeline = MagicMock()
        expected_pipeline_result = {"status": "executed", "hash": uuid.uuid4().hex}
        mock_pipeline.execute.return_value = expected_pipeline_result

        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=mock_advisor,
            pipeline=mock_pipeline
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
        self.assertEqual(result["stress_pipeline_result"], expected_pipeline_result)

    def test_synchronize_missing_attributes_fix(self):
        mock_advisor = MagicMock()
        mock_advisor.monitor = None
        mock_advisor.rebalancer = None

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"status": uuid.uuid4().hex}

        custom_monitor = DummyMonitor()
        custom_rebalancer = DummyRebalancer()

        syncer = MarketPortfolioStressAutoHedgeSync(
            monitor=custom_monitor,
            rebalancer=custom_rebalancer,
            advisor=mock_advisor,
            pipeline=mock_pipeline
        )

        syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(mock_advisor.monitor, custom_monitor)
        self.assertEqual(mock_advisor.rebalancer, custom_rebalancer)

    def test_run_auto_hedge_sync_wrapper(self):
        db_storage = MagicMock()
        monitor = MagicMock()
        evaluator = MagicMock()
        rebalancer = MagicMock()
        storage_file = uuid.uuid4().hex + ".json"

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncerClass:
            instance = MockSyncerClass.return_value
            expected_output = {"status": "success", "token": uuid.uuid4().hex}
            instance.synchronize.return_value = expected_output

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

            MockSyncerClass.assert_called_once_with(
                db_storage=db_storage,
                monitor=monitor,
                evaluator=evaluator,
                rebalancer=rebalancer,
                storage_file=storage_file
            )
            instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_output)


if __name__ == "__main__":
    unittest.main()