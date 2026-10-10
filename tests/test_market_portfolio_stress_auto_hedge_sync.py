import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync, run_auto_hedge_sync


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = random.uniform(1.0, 50.0)
        self.shifts = [random.uniform(-10.0, 10.0) for _ in range(3)]
        self.storage_file = f"temp_{uuid.uuid4().hex}.json"

    def test_synchronize_success(self):
        mock_advisor = MagicMock()
        expected_rec_key = uuid.uuid4().hex
        expected_rec_val = uuid.uuid4().hex
        mock_advisor.analyze_and_recommend.return_value = {expected_rec_key: expected_rec_val}

        mock_pipeline = MagicMock()
        expected_pipeline_key = uuid.uuid4().hex
        expected_pipeline_val = uuid.uuid4().hex
        mock_pipeline.execute.return_value = {expected_pipeline_key: expected_pipeline_val}

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

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["advisor_recommendation"][expected_rec_key], expected_rec_val)
        self.assertEqual(result["stress_pipeline_result"][expected_pipeline_key], expected_pipeline_val)

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_synchronize_advisor_exception_resilience(self):
        mock_advisor = MagicMock()
        error_message = uuid.uuid4().hex
        mock_advisor.analyze_and_recommend.side_effect = Exception(error_message)

        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

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

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertIn("error", result)
        self.assertIn(error_message, result["error"])

    def test_synchronize_validation_error_invalid_percentage(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        invalid_percentage = random.choice([-5.0, 105.0, 0.0])

        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=invalid_percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("percentage", result["error"].lower())

    def test_synchronize_validation_error_invalid_shifts(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )

        invalid_shifts = "not_a_list"

        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=invalid_shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("shifts", result["error"].lower())

    def test_run_auto_hedge_sync_wrapper(self):
        mock_db = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        mock_rebalancer = MagicMock()

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as MockSyncerClass:
            mock_instance = MockSyncerClass.return_value
            expected_res_key = uuid.uuid4().hex
            expected_res_val = uuid.uuid4().hex
            mock_instance.synchronize.return_value = {expected_res_key: expected_res_val}

            res = run_auto_hedge_sync(
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

            MockSyncerClass.assert_called_once_with(
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

            self.assertEqual(res[expected_res_key], expected_res_val)

    def test_stream_handler_integration_mock(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            storage_file=self.storage_file
        )
        
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        syncer.stream_handler = stream_data
        
        self.assertEqual(syncer.stream_handler.read(), stream_data.getvalue())


if __name__ == "__main__":
    unittest.main()