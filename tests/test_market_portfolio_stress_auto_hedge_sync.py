import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import string
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    run_auto_hedge_sync,
    DummyMonitor,
    DummyRebalancer
)


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 99.9), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 5))]
        
        self.mock_advisor = MagicMock()
        self.mock_pipeline = MagicMock()
        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_rebalancer = MagicMock()

    def test_synchronize_invalid_shifts_format(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        invalid_shifts = ''.join(random.choices(string.ascii_letters, k=8))
        
        result = syncer.synchronize(
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
        self.mock_advisor.analyze_and_recommend.assert_not_called()
        self.mock_pipeline.execute.assert_not_called()

    def test_synchronize_invalid_percentage_bounds(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        invalid_pct = random.choice([-5.0, 0.0, 105.5])

        result = syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=invalid_pct,
            shifts=self.shifts
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertIn("Invalid percentage", result["error"])
        self.mock_advisor.analyze_and_recommend.assert_not_called()
        self.mock_pipeline.execute.assert_not_called()

    def test_synchronize_advisor_exception_handling(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
        )
        exception_msg = uuid.uuid4().hex
        self.mock_advisor.analyze_and_recommend.side_effect = Exception(exception_msg)

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
        self.assertEqual(result["error"], exception_msg)
        self.mock_pipeline.execute.assert_not_called()

    def test_synchronize_success_flow(self):
        advisor_rec = {"status": "ok", "action": uuid.uuid4().hex}
        pipeline_res = {"executed": True, "details": uuid.uuid4().hex}

        self.mock_advisor.analyze_and_recommend.return_value = advisor_rec
        self.mock_pipeline.execute.return_value = pipeline_res

        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=self.mock_advisor,
            pipeline=self.mock_pipeline
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
        self.assertEqual(result["advisor_recommendation"], {**advisor_rec, "portfolio_id": self.portfolio_id})
        self.assertEqual(result["stress_pipeline_result"], pipeline_res)

        self.mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id
        )
        self.mock_pipeline.execute.assert_called_once_with(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

    def test_run_auto_hedge_sync_wrapper(self):
        storage_file_path = uuid.uuid4().hex
        expected_pipeline_output = {"pipeline_status": uuid.uuid4().hex}
        expected_advisor_output = {"advisor_status": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor') as mock_advisor_cls, \
             patch('skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline') as mock_pipeline_cls:
            
            instance_advisor = mock_advisor_cls.return_value
            instance_advisor.analyze_and_recommend.return_value = expected_advisor_output

            instance_pipeline = mock_pipeline_cls.return_value
            instance_pipeline.execute.return_value = expected_pipeline_output

            result = run_auto_hedge_sync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=None,
                rebalancer=self.mock_rebalancer,
                storage_file=storage_file_path,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["request_id"], self.request_id)
            self.assertEqual(result["stress_pipeline_result"], expected_pipeline_output)
            self.assertEqual(result["advisor_recommendation"]["portfolio_id"], self.portfolio_id)

    def test_dummy_monitor_and_rebalancer_behavior(self):
        monitor = DummyMonitor()
        rebalancer = DummyRebalancer()
        
        mon_res = monitor.get_portfolio_state(self.portfolio_id)
        self.assertEqual(mon_res["portfolio_id"], self.portfolio_id)
        self.assertEqual(mon_res["status"], "active")

        status_data = {"action": uuid.uuid4().hex}
        reb_res = rebalancer.set_trigger_status(self.portfolio_id, status_data)
        self.assertEqual(reb_res["portfolio_id"], self.portfolio_id)
        self.assertEqual(reb_res["status"], "updated")
        self.assertEqual(reb_res["data"], status_data)