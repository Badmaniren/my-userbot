import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline,
    ExecutionPipelineError
)

class TestMarketPortfolioExecutionPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.volume = random.uniform(100.0, 10000.0)
        self.percentage = random.uniform(-10.0, 10.0)
        self.scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"
        self.simulation_id = uuid.uuid4().hex

    def test_pipeline_initialization(self):
        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        self.assertEqual(pipeline.storage_file, self.storage_file)
        self.assertIsNotNone(pipeline.slippage_model)
        self.assertIsNotNone(pipeline.scenario_simulator)

    @patch('skills.market_portfolio_execution_pipeline.MarketPortfolioSlippageModel')
    @patch('skills.market_portfolio_execution_pipeline.PortfolioScenarioSimulator')
    def test_execute_order_simulation_success(self, mock_simulator_cls, mock_slippage_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_slippage = mock_slippage_cls.return_value

        expected_scenario_res = {
            "symbol": self.ticker,
            "percentage": self.percentage,
            "simulated_price": random.uniform(50.0, 500.0)
        }
        mock_simulator.simulate_scenario.return_value = expected_scenario_res

        expected_slippage_res = {
            "order_id": self.simulation_id,
            "executed_price": random.uniform(50.0, 500.0),
            "slippage": random.uniform(0.1, 5.0)
        }
        mock_slippage.simulate_order_execution.return_value = expected_slippage_res
        mock_slippage.persist_execution_logs.return_value = True

        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        order_data = {"ticker": self.ticker, "volume": self.volume}
        market_context = {"liquidity_tier": "high"}

        result = pipeline.execute_order_simulation(order_data, market_context, self.percentage)

        self.assertIn("scenario_result", result)
        self.assertIn("execution_result", result)
        self.assertEqual(result["scenario_result"], expected_scenario_res)
        self.assertEqual(result["execution_result"], expected_slippage_res)

        mock_simulator.simulate_scenario.assert_called_once()
        mock_slippage.simulate_order_execution.assert_called_once()
        mock_slippage.persist_execution_logs.assert_called_once()

    @patch('skills.market_portfolio_execution_pipeline.PortfolioScenarioSimulator')
    def test_execute_order_simulation_scenario_failure(self, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_simulator.simulate_scenario.side_effect = Exception("Scenario failure")

        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        order_data = {"ticker": self.ticker, "volume": self.volume}
        market_context = {}

        with self.assertRaises(ExecutionPipelineError):
            pipeline.execute_order_simulation(order_data, market_context, self.percentage)

    @patch('skills.market_portfolio_execution_pipeline.MarketPortfolioSlippageModel')
    @patch('skills.market_portfolio_execution_pipeline.PortfolioScenarioSimulator')
    def test_run_batch_pipeline_execution(self, mock_simulator_cls, mock_slippage_cls):
        mock_slippage = mock_slippage_cls.return_value
        
        batch_size = random.randint(2, 5)
        orders = [{"ticker": ''.join(random.choices(string.ascii_uppercase, k=3)), "volume": random.uniform(10, 100)} for _ in range(batch_size)]
        contexts = [{"context_id": uuid.uuid4().hex} for _ in range(batch_size)]
        
        expected_batch_results = [{"status": "executed", "id": uuid.uuid4().hex} for _ in range(batch_size)]
        mock_slippage.simulate_batch.return_value = expected_batch_results
        mock_slippage.persist_execution_logs.return_value = True

        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        res = pipeline.run_batch_pipeline_execution(orders, contexts, self.percentage)

        self.assertEqual(res, expected_batch_results)
        mock_slippage.simulate_batch.assert_called_once_with(orders, contexts)
        mock_slippage.persist_execution_logs.assert_called_once()

    @patch('skills.market_portfolio_execution_pipeline.MarketPortfolioSlippageModel')
    @patch('skills.market_portfolio_execution_pipeline.PortfolioScenarioSimulator')
    def test_run_stress_pipeline(self, mock_simulator_cls, mock_slippage_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_slippage = mock_slippage_cls.return_value

        shifts = [random.uniform(-5.0, 5.0) for _ in range(3)]
        stress_scenario_res = {"stress_passed": True, "shifts": shifts}
        mock_simulator.run_stress_test.return_value = stress_scenario_res

        stress_slippage_res = {"stress_slippage_factor": random.uniform(0.01, 0.5)}
        mock_slippage.simulate_stress_slippage.return_value = stress_slippage_res

        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        result = pipeline.run_stress_pipeline(self.ticker, shifts, self.volume, self.scenario_name)

        self.assertIn("stress_scenario", result)
        self.assertIn("stress_slippage", result)
        self.assertEqual(result["stress_scenario"], stress_scenario_res)
        self.assertEqual(result["stress_slippage"], stress_slippage_res)

        mock_simulator.run_stress_test.assert_called_once_with(self.ticker, shifts)
        mock_slippage.simulate_stress_slippage.assert_called_once_with(self.ticker, self.volume, self.scenario_name)

    @patch('skills.market_portfolio_execution_pipeline.MarketPortfolioSlippageModel')
    def test_get_historical_pipeline_logs(self, mock_slippage_cls):
        mock_slippage = mock_slippage_cls.return_value
        expected_logs = [{"log_id": uuid.uuid4().hex, "action": "simulate"} for _ in range(3)]
        mock_slippage.get_execution_logs.return_value = expected_logs

        pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        logs = pipeline.get_historical_pipeline_logs(self.simulation_id)

        self.assertEqual(logs, expected_logs)
        mock_slippage.get_execution_logs.assert_called_once_with(self.simulation_id, self.storage_file)

if __name__ == '__main__':
    unittest.main()