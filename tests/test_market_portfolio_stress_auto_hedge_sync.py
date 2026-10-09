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
        self.rand_portfolio_id = str(uuid.uuid4())
        self.rand_request_id = str(uuid.uuid4())
        self.rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.rand_percentage = round(random.uniform(1.0, 99.9), 2)
        self.rand_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        
        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()
        self.rand_storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        state = monitor.get_portfolio_state(self.rand_portfolio_id)
        self.assertEqual(state["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        rand_data = {"action": uuid.uuid4().hex}
        res = rebalancer.set_trigger_status(self.rand_portfolio_id, rand_data)
        self.assertEqual(res["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], rand_data)

    def test_synchronize_execution(self):
        mock_advisor = MagicMock()
        rand_recommendation = {"advice": uuid.uuid4().hex}
        mock_advisor.analyze_and_recommend.return_value = rand_recommendation

        mock_pipeline = MagicMock()
        rand_pipeline_res = {"pipeline_status": uuid.uuid4().hex}
        mock_pipeline.execute.return_value = rand_pipeline_res

        syncer = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=self.mock_monitor,
            evaluator=self.mock_evaluator,
            rebalancer=self.mock_rebalancer,
            storage_file=self.rand_storage_file,
            advisor=mock_advisor,
            pipeline=mock_pipeline
        )

        result = syncer.synchronize(
            portfolio_id=self.rand_portfolio_id,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["request_id"], self.rand_request_id)
        self.assertEqual(result["advisor_recommendation"], rand_recommendation)
        self.assertEqual(result["stress_pipeline_result"], rand_pipeline_res)

        mock_advisor.analyze_and_recommend.assert_called_once_with(
            portfolio_id=self.rand_portfolio_id,
            request_id=self.rand_request_id
        )
        mock_pipeline.execute.assert_called_once_with(
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

    def test_synchronize_fallback_initialization(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=None,
            evaluator=self.mock_evaluator,
            rebalancer=None,
            storage_file=self.rand_storage_file
        )
        
        self.assertIsNotNone(syncer.monitor)
        self.assertIsNotNone(syncer.rebalancer)
        self.assertIsNotNone(syncer.advisor)
        self.assertIsNotNone(syncer.pipeline)

        syncer.advisor.analyze_and_recommend = MagicMock(return_value={"test": uuid.uuid4().hex})
        syncer.pipeline.execute = MagicMock(return_value={"test2": uuid.uuid4().hex})

        result = syncer.synchronize(
            portfolio_id=self.rand_portfolio_id,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)

    def test_run_auto_hedge_sync_wrapper(self):
        rand_rec = {"msg": uuid.uuid4().hex}
        rand_pipe = {"msg2": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor") as mock_adv_cls, \
             patch("skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline") as mock_pipe_cls:
            
            mock_adv_instance = mock_adv_cls.return_value
            mock_adv_instance.analyze_and_recommend.return_value = rand_rec

            mock_pipe_instance = mock_pipe_cls.return_value
            mock_pipe_instance.execute.return_value = rand_pipe

            result = run_auto_hedge_sync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
                storage_file=self.rand_storage_file,
                portfolio_id=self.rand_portfolio_id,
                request_id=self.rand_request_id,
                symbol=self.rand_symbol,
                percentage=self.rand_percentage,
                shifts=self.rand_shifts
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
            self.assertEqual(result["request_id"], self.rand_request_id)
            self.assertEqual(result["advisor_recommendation"], rand_rec)
            self.assertEqual(result["stress_pipeline_result"], rand_pipe)


if __name__ == "__main__":
    unittest.main()