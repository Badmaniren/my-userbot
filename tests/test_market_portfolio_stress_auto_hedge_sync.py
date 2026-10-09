import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
    run_auto_hedge_sync
)
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        
        self.mock_db_storage = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()

    def test_auto_hedge_sync_composition_success(self):
        expected_advice = {
            "action": ''.join(random.choices(string.ascii_lowercase, k=8)),
            "hedge_ratio": random.random()
        }
        expected_pipeline_result = {
            "status": ''.join(random.choices(string.ascii_lowercase, k=6)),
            "impact": random.uniform(-100, 0)
        }

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor') as MockAdvisor, \
             patch('skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline') as MockPipeline:

            instance_advisor = MockAdvisor.return_value
            instance_advisor.analyze_and_recommend.return_value = expected_advice

            instance_pipeline = MockPipeline.return_value
            instance_pipeline.execute.return_value = expected_pipeline_result

            syncer = MarketPortfolioStressAutoHedgeSync(
                db_storage=self.mock_db_storage,
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

            MockAdvisor.assert_called_once_with(
                db_storage=self.mock_db_storage,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer
            )
            instance_advisor.analyze_and_recommend.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id
            )

            MockPipeline.assert_called_once_with(storage_file=self.storage_file)
            instance_pipeline.execute.assert_called_once_with(
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertIn("advisor_recommendation", result)
            self.assertIn("stress_pipeline_result", result)
            self.assertEqual(result["advisor_recommendation"], expected_advice)
            self.assertEqual(result["stress_pipeline_result"], expected_pipeline_result)

    def test_run_auto_hedge_sync_wrapper(self):
        random_sync_result = {
            str(uuid.uuid4()): str(uuid.uuid4())
        }

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressAutoHedgeSync') as MockSyncClass:
            instance = MockSyncClass.return_value
            instance.synchronize.return_value = random_sync_result

            res = run_auto_hedge_sync(
                db_storage=self.mock_db_storage,
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

            instance.synchronize.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )
            self.assertEqual(res, random_sync_result)

    def test_sync_io_stream_handling(self):
        garbage_bytes = ''.join(random.choices(string.printable, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(garbage_bytes)

        with patch('skills.market_portfolio_stress_auto_hedge_sync.MarketPortfolioStressHedgeAdvisor') as MockAdvisor, \
             patch('skills.market_portfolio_stress_auto_hedge_sync.PortfolioStressScenarioPipeline') as MockPipeline:

            syncer = MarketPortfolioStressAutoHedgeSync(
                db_storage=self.mock_db_storage,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
                storage_file=self.storage_file
            )

            syncer.stream_handler = mock_stream
            read_data = syncer.stream_handler.read()

            self.assertEqual(read_data, garbage_bytes)


if __name__ == '__main__':
    unittest.main()