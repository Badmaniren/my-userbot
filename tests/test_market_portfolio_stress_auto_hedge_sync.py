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
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        res = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        data_payload = {"action": uuid.uuid4().hex}
        res = rebalancer.set_trigger_status(self.portfolio_id, data_payload)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], data_payload)

    def test_synchronize_execution_success(self):
        mock_advisor = MagicMock()
        expected_rec = {"advice_id": uuid.uuid4().hex, "action": "hedge"}
        mock_advisor.analyze_and_recommend.return_value = expected_rec

        mock_pipeline = MagicMock()
        expected_pipeline_res = {"pipeline_status": "ok", "metric": random.randint(100, 999)}
        mock_pipeline.execute.return_value = expected_pipeline_res

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
        self.assertEqual(result["advisor_recommendation"], expected_rec)
        self.assertEqual(result["stress_pipeline_result"], expected_pipeline_res)

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
        raw_rec = {"some_field": uuid.uuid4().hex}
        mock_advisor.analyze_and_recommend.return_value = raw_rec

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {}

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

    def test_run_auto_hedge_sync_wrapper(self):
        db_storage_mock = MagicMock()
        monitor_mock = MagicMock()
        evaluator_mock = MagicMock()
        rebalancer_mock = MagicMock()

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncClass:
            instance_mock = MockSyncClass.return_value
            expected_output = {"status": uuid.uuid4().hex}
            instance_mock.synchronize.return_value = expected_output

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

            MockSyncClass.assert_called_once_with(
                db_storage=db_storage_mock,
                monitor=monitor_mock,
                evaluator=evaluator_mock,
                rebalancer=rebalancer_mock,
                storage_file=self.storage_file
            )
            instance_mock.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_output)


if __name__ == "__main__":
    unittest.main()