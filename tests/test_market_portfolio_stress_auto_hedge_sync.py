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
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(2, 5))]
        
        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"

    def test_dummy_monitor_behavior(self):
        monitor = DummyMonitor()
        pid = str(uuid.uuid4())
        state = monitor.get_portfolio_state(pid)
        self.assertEqual(state["portfolio_id"], pid)
        self.assertEqual(state["status"], "active")

    def test_dummy_rebalancer_behavior(self):
        rebalancer = DummyRebalancer()
        pid = str(uuid.uuid4())
        rand_data = {"threshold": random.randint(10, 100)}
        res = rebalancer.set_trigger_status(pid, rand_data)
        self.assertEqual(res["portfolio_id"], pid)
        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["data"], rand_data)

    def test_synchronize_execution_flow(self):
        advisor_mock_result = {
            "advice_id": str(uuid.uuid4()),
            "action": random.choice(["hedge", "rebalance", "hold"])
        }
        pipeline_mock_result = {
            "pipeline_id": str(uuid.uuid4()),
            "executed": True,
            "metrics": {"score": random.random()}
        }

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor') as MockAdvisorClass, \
             patch('skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline') as MockPipelineClass:
            
            advisor_instance = MockAdvisorClass.return_value
            advisor_instance.analyze_and_recommend.return_value = advisor_mock_result

            pipeline_instance = MockPipelineClass.return_value
            pipeline_instance.execute.return_value = pipeline_mock_result

            syncer = MarketPortfolioStressAutoHedgeSync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
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
            self.assertEqual(result["advisor_recommendation"], advisor_mock_result)
            self.assertEqual(result["stress_pipeline_result"], pipeline_mock_result)

            advisor_instance.analyze_and_recommend.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id
            )
            pipeline_instance.execute.assert_called_once_with(
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

    def test_run_auto_hedge_sync_wrapper(self):
        expected_recommendation = {"action": "sync", "value": random.randint(1, 1000)}
        expected_pipeline_data = {"simulation": "completed", "code": random.randint(200, 500)}

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor') as MockAdvisorClass, \
             patch('skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline') as MockPipelineClass:

            MockAdvisorClass.return_value.analyze_and_recommend.return_value = expected_recommendation
            MockPipelineClass.return_value.execute.return_value = expected_pipeline_data

            result = run_auto_hedge_sync(
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

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["request_id"], self.request_id)
            self.assertEqual(result["advisor_recommendation"], expected_recommendation)
            self.assertEqual(result["stress_pipeline_result"], expected_pipeline_data)

    def test_advisor_dependency_healing(self):
        syncer = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.mock_db,
            monitor=None,
            evaluator=self.mock_evaluator,
            rebalancer=None,
            storage_file=self.storage_file
        )
        
        syncer.advisor.monitor = None
        syncer.advisor.rebalancer = None

        with patch.object(syncer.advisor, 'analyze_and_recommend') as mock_analyze, \
             patch.object(syncer.pipeline, 'execute') as mock_execute:
            
            mock_analyze.return_value = {"fixed": True}
            mock_execute.return_value = {"ok": True}

            syncer.synchronize(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIsNotNone(syncer.advisor.monitor)
            self.assertIsNotNone(syncer.advisor.rebalancer)


if __name__ == '__main__':
    unittest.main()