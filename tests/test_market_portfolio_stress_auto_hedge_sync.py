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

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertIsInstance(state, dict)
        self.assertEqual(state.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(state.get("status"), "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        status_data = {"action": ''.join(random.choices(string.ascii_lowercase, k=8))}
        res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("status"), "updated")
        self.assertEqual(res.get("data"), status_data)

    def test_synchronize_success_flow(self):
        mock_advisor = MagicMock()
        expected_recommendation = {"action": ''.join(random.choices(string.ascii_lowercase, k=6))}
        mock_advisor.analyze_and_recommend.return_value = expected_recommendation

        mock_pipeline = MagicMock()
        expected_pipeline_result = {"pipeline_status": ''.join(random.choices(string.ascii_lowercase, k=6))}
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

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        
        rec = result.get("advisor_recommendation")
        self.assertIsInstance(rec, dict)
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

    def test_synchronize_advisor_missing_portfolio_id(self):
        mock_advisor = MagicMock()
        mock_advisor.analyze_and_recommend.return_value = {"metric": random.randint(100, 999)}

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"executed": True}

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

        self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)

    def test_run_auto_hedge_sync_wrapper(self):
        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync') as MockSyncerClass:
            instance_mock = MockSyncerClass.return_value
            expected_output = {"status": ''.join(random.choices(string.ascii_lowercase, k=5))}
            instance_mock.synchronize.return_value = expected_output

            db = MagicMock()
            mon = MagicMock()
            ev = MagicMock()
            reb = MagicMock()
            st_file = ''.join(random.choices(string.ascii_lowercase, k=10)) + ".json"

            res = run_auto_hedge_sync(
                db_storage=db,
                monitor=mon,
                evaluator=ev,
                rebalancer=reb,
                storage_file=st_file,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            MockSyncerClass.assert_called_once_with(
                db_storage=db,
                monitor=mon,
                evaluator=ev,
                rebalancer=reb,
                storage_file=st_file
            )
            instance_mock.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_output)


if __name__ == '__main__':
    unittest.main()