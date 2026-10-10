import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    DummyMonitor,
    DummyRebalancer,
    run_auto_hedge_sync
)


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [random.randint(-10, 10), random.randint(-20, 20)]
        self.storage_file = f"{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertIsInstance(state, dict)
        self.assertEqual(state.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(state.get("status"), "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": uuid.uuid4().hex}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("status"), "updated")
        self.assertEqual(res.get("data"), status_data)

    def test_auto_hedge_sync_initialization_defaults(self):
        syncer = MarketPortfolioStressAutoHedgeSync(storage_file=self.storage_file)
        self.assertIsInstance(syncer.monitor, DummyMonitor)
        self.assertIsInstance(syncer.rebalancer, DummyRebalancer)
        self.assertIsNotNone(syncer.advisor)
        self.assertIsNotNone(syncer.pipeline)

    def test_synchronize_execution_flow(self):
        mock_advisor = MagicMock()
        expected_recommendation = {"action": uuid.uuid4().hex, "weight": random.random()}
        mock_advisor.analyze_and_recommend.return_value = expected_recommendation

        mock_pipeline = MagicMock()
        expected_pipeline_result = {"pipeline_status": uuid.uuid4().hex}
        mock_pipeline.execute.return_value = expected_pipeline_result

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

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        
        rec = result.get("advisor_recommendation")
        self.assertEqual(rec.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(rec.get("action"), expected_recommendation["action"])
        
        self.assertEqual(result.get("stress_pipeline_result"), expected_pipeline_result)

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_synchronize_missing_portfolio_id_in_recommendation(self):
        mock_advisor = MagicMock()
        raw_recommendation = {"metric": uuid.uuid4().hex}
        mock_advisor.analyze_and_recommend.return_value = raw_recommendation

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"executed": True}

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

        rec = result.get("advisor_recommendation")
        self.assertEqual(rec.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(rec.get("metric"), raw_recommendation["metric"])

    def test_run_auto_hedge_sync_wrapper(self):
        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncerClass:
            mock_instance = MagicMock()
            expected_output = {"run_id": uuid.uuid4().hex}
            mock_instance.synchronize.return_value = expected_output
            MockSyncerClass.return_value = mock_instance

            db_storage = MagicMock()
            monitor = MagicMock()
            evaluator = MagicMock()
            rebalancer = MagicMock()

            res = run_auto_hedge_sync(
                db_storage=db_storage,
                monitor=monitor,
                evaluator=evaluator,
                rebalancer=rebalancer,
                storage_file=self.storage_file,
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