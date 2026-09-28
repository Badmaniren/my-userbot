import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline, ExecutionPipelineError
from skills.market_portfolio_rebalance_planner import MarketPortfolioRebalancePlanner

class TestMarketPortfolioRebalancePlanner(unittest.TestCase):

    def setUp(self):
        self.storage_path = f"/tmp/{uuid.uuid4().hex}.db"
        self.planner = MarketPortfolioRebalancePlanner(self.storage_path)

    def test_rebalance_flow_success(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        shifts = random.randint(1, 100)
        percentage = random.uniform(0.01, 0.99)

        mock_optimizer_result = {"target_allocation": random.random(), "status": "optimized"}
        mock_execution_result = {"order_id": uuid.uuid4().hex, "status": "executed"}

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.optimize_strategy') as mock_opt:
            with patch('skills.market_portfolio_execution_pipeline.MarketPortfolioExecutionPipeline.execute_order_simulation') as mock_exec:
                mock_opt.return_value = mock_optimizer_result
                mock_exec.return_value = mock_execution_result

                result = self.planner.plan_and_execute(symbol, shifts, percentage)

                self.assertEqual(result['execution_id'], mock_execution_result['order_id'])
                mock_opt.assert_called_once_with(symbol, shifts, percentage)
                mock_exec.assert_called_once()

    def test_rebalance_execution_failure(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        shifts = random.randint(10, 50)
        percentage = random.random()

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.optimize_strategy') as mock_opt:
            with patch('skills.market_portfolio_execution_pipeline.MarketPortfolioExecutionPipeline.execute_order_simulation') as mock_exec:
                mock_opt.return_value = {"allocation": 0.5}
                mock_exec.side_effect = ExecutionPipelineError("Execution failed")

                with self.assertRaises(ExecutionPipelineError):
                    self.planner.plan_and_execute(symbol, shifts, percentage)

    def test_batch_rebalance_integrity(self):
        batch_size = random.randint(2, 5)
        symbols = [''.join(random.choices(string.ascii_uppercase, k=4)) for _ in range(batch_size)]
        percentage = random.random()

        expected_batch_results = [{"id": uuid.uuid4().hex} for _ in range(batch_size)]

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.optimize_and_evaluate') as mock_opt:
            with patch('skills.market_portfolio_execution_pipeline.MarketPortfolioExecutionPipeline.run_batch_pipeline_execution') as mock_exec:
                mock_exec.return_value = expected_batch_results

                results = self.planner.run_batch_rebalance(symbols, percentage)

                self.assertEqual(len(results), batch_size)
                self.assertEqual(results[0]['id'], expected_batch_results[0]['id'])
                mock_exec.assert_called_once()

    def test_strategy_summary_retrieval(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_summary = {"volatility": random.random(), "score": random.randint(1, 100)}

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.get_strategy_summary') as mock_summary:
            mock_summary.return_value = random_summary

            data = self.planner.get_rebalance_readiness(symbol)

            self.assertEqual(data['score'], random_summary['score'])
            mock_summary.assert_called_with(symbol)

    def test_stress_recovery_integration(self):
        ticker = ''.join(random.choices(string.ascii_uppercase, k=3))
        shifts = [random.uniform(-0.1, 0.1) for _ in range(3)]
        volume = random.randint(100, 1000)
        scenario = uuid.uuid4().hex

        with patch('skills.market_portfolio_execution_pipeline.MarketPortfolioExecutionPipeline.run_stress_pipeline') as mock_stress:
            mock_stress.return_value = {"stress_test_id": scenario, "result": "passed"}

            report = self.planner.verify_stress_resilience(ticker, shifts, volume, scenario)

            self.assertEqual(report['stress_test_id'], scenario)
            mock_stress.assert_called_once_with(ticker, shifts, volume, scenario)

if __name__ == '__main__':
    unittest.main()