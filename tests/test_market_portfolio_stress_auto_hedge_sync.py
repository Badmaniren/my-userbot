import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    run_auto_hedge_sync,
)


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_synchronize_success(self):
        mock_advisor = MagicMock()
        expected_rec = {str(uuid.uuid4()): "".join(random.choices(string.ascii_letters, k=10))}
        mock_advisor.analyze_and_recommend.return_value = expected_rec

        mock_pipeline = MagicMock()
        expected_pipeline_res = {str(uuid.uuid4()): random.randint(100, 999)}
        mock_pipeline.execute.return_value = expected_pipeline_res

        mock_monitor = MagicMock()
        mock_rebalancer = MagicMock()

        syncer = MarketPortfolioStressAutoHedgeSync(
            db_storage=MagicMock(),
            monitor=mock_monitor,
            evaluator=MagicMock(),
            rebalancer=mock_rebalancer,
            storage_file=self.storage_file,
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
        
        expected_recommendation = expected_rec.copy()
        expected_recommendation["portfolio_id"] = self.portfolio_id
        self.assertEqual(result["advisor_recommendation"], expected_recommendation)
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

    def test_synchronize_adds_portfolio_id_if_missing(self):
        mock_advisor = MagicMock()
        mock_advisor.analyze_and_recommend.return_value = {"action": "".join(random.choices(string.ascii_lowercase, k=8))}

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"pipeline_status": "ok"}

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
        db_storage = MagicMock()
        monitor = MagicMock()
        evaluator = MagicMock()
        rebalancer = MagicMock()
        storage_file = f"/tmp/{uuid.uuid4().hex}.json"

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncerClass:
            instance_mock = MockSyncerClass.return_value
            expected_return = {
                "status": "success",
                "portfolio_id": self.portfolio_id,
                "request_id": self.request_id,
                "advisor_recommendation": {},
                "stress_pipeline_result": {}
            }
            instance_mock.synchronize.return_value = expected_return

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
            instance_mock.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, expected_return)

    def test_synchronize_restores_missing_advisor_dependencies(self):
        mock_advisor = MagicMock()
        mock_advisor.monitor = None
        mock_advisor.rebalancer = None

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {}

        monitor_obj = MagicMock()
        rebalancer_obj = MagicMock()

        syncer = MarketPortfolioStressAutoHedgeSync(
            monitor=monitor_obj,
            rebalancer=rebalancer_obj,
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

        self.assertEqual(mock_advisor.monitor, monitor_obj)
        self.assertEqual(mock_advisor.rebalancer, rebalancer_obj)


if __name__ == "__main__":
    unittest.main()