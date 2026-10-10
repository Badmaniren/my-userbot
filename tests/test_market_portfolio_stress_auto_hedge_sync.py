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
        self.percentage = round(random.uniform(1.0, 99.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"
        
        self.mock_advisor = MagicMock()
        self.mock_pipeline = MagicMock()

    def test_synchronization_invalid_shifts_type(self):
        sync_instance = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            storage_file=self.storage_file,
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        invalid_shifts = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        result = sync_instance.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=invalid_shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertIn("Invalid shifts format", result["error"])

    def test_synchronization_invalid_percentage_bounds(self):
        sync_instance = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            storage_file=self.storage_file,
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        invalid_percentage = random.choice([-5.0, 0.0, 105.0, 200.0])

        result = sync_instance.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=invalid_percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertIn("Invalid percentage", result["error"])

    def test_synchronization_advisor_exception_handling(self):
        sync_instance = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            storage_file=self.storage_file,
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        error_message = f"AdvisorFailure_{uuid.uuid4().hex}"
        self.mock_advisor.analyze_and_recommend.side_effect = Exception(error_message)

        result = sync_instance.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["error"], error_message)

    def test_synchronization_success_flow(self):
        sync_instance = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            storage_file=self.storage_file,
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )

        advisor_payload = {"action": "hedge", "metric": random.uniform(0.1, 0.9)}
        pipeline_payload = {"executed": True, "details": uuid.uuid4().hex}

        self.mock_advisor.analyze_and_recommend.return_value = advisor_payload
        self.mock_pipeline.execute.return_value = pipeline_payload

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
        self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["advisor_recommendation"]["action"], advisor_payload["action"])
        self.assertEqual(result["stress_pipeline_result"], pipeline_payload)

        self.mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        self.mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_run_auto_hedge_sync_helper(self):
        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync") as mock_cls:
            mock_instance = MagicMock()
            expected_output = {"status": "success", "id": uuid.uuid4().hex}
            mock_instance.synchronize.return_value = expected_output
            mock_cls.return_value = mock_instance

            res = run_auto_hedge_sync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
                storage_file=self.storage_file,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_cls.assert_called_once_with(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
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

    def test_dummy_monitor_and_rebalancer(self):
        monitor = DummyMonitor()
        mon_state = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(mon_state["portfolio_id"], self.portfolio_id)
        self.assertEqual(mon_state["status"], "active")

        rebalancer = DummyRebalancer()
        status_data = {"risk_level": uuid.uuid4().hex}
        reb_res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertEqual(reb_res["portfolio_id"], self.portfolio_id)
        self.assertEqual(reb_res["status"], "updated")
        self.assertEqual(reb_res["data"], status_data)


if __name__ == "__main__":
    unittest.main()