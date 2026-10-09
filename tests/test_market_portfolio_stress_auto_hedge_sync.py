import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync, DummyMonitor, DummyRebalancer


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertIsInstance(state, dict)
        self.assertEqual(state["portfolio_id"], self.portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": "".join(random.choices(string.ascii_lowercase, k=6))}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], status_data)

    def test_synchronize_success_flow(self):
        mock_advisor = MagicMock()
        rec_data = {"recommendation": "".join(random.choices(string.ascii_lowercase, k=10))}
        mock_advisor.analyze_and_recommend.return_value = rec_data

        mock_pipeline = MagicMock()
        pipe_result = {"pipeline_status": "executed", "value": random.randint(100, 999)}
        mock_pipeline.execute.return_value = pipe_result

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

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["stress_pipeline_result"], pipe_result)
        self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["advisor_recommendation"]["recommendation"], rec_data["recommendation"])

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_synchronize_injects_portfolio_id_if_missing(self):
        mock_advisor = MagicMock()
        mock_advisor.analyze_and_recommend.return_value = {"key": "value"}

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"metrics": random.random()}

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

        self.assertIn("portfolio_id", result["advisor_recommendation"])
        self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["advisor_recommendation"]["key"], "value")

    def test_run_auto_hedge_sync_wrapper(self):
        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync') as MockSyncerClass:
            mock_instance = MockSyncerClass.return_value
            expected_output = {
                "status": "success",
                "portfolio_id": self.portfolio_id,
                "request_id": self.request_id,
                "advisor_recommendation": {},
                "stress_pipeline_result": {}
            }
            mock_instance.synchronize.return_value = expected_output

            db_storage_mock = MagicMock()
            monitor_mock = MagicMock()
            evaluator_mock = MagicMock()
            rebalancer_mock = MagicMock()
            storage_file_mock = f"/tmp/{uuid.uuid4().hex}.json"

            res = run_auto_hedge_sync(
                db_storage=db_storage_mock,
                monitor=monitor_mock,
                evaluator=evaluator_mock,
                rebalancer=rebalancer_mock,
                storage_file=storage_file_mock,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            MockSyncerClass.assert_called_once_with(
                db_storage=db_storage_mock,
                monitor=monitor_mock,
                evaluator=evaluator_mock,
                rebalancer=rebalancer_mock,
                storage_file=storage_file_mock
            )
            mock_instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_output)


if __name__ == '__main__':
    unittest.main()