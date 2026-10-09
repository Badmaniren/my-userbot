import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_backtest_aggregator import aggregate_stress_backtest_report, MarketPortfolioStressBacktestAggregator


class TestMarketPortfolioStressBacktestAggregator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [random.randint(-20, 20), random.randint(-10, 10)]

    def test_aggregator_class_composition_and_logic(self):
        mock_pipeline_result = {
            "status": "success",
            "pipeline_id": uuid.uuid4().hex,
            "metrics": {
                "max_drawdown": random.uniform(-40.0, -5.0),
                "volatility": random.uniform(0.1, 0.9)
            }
        }

        mock_simulator_result = {
            "simulation_id": uuid.uuid4().hex,
            "final_value": random.uniform(1000.0, 100000.0),
            "stress_results": {str(s): random.uniform(-0.5, 0.5) for s in self.shifts}
        }

        with patch('skills.market_portfolio_stress_backtest_aggregator.PortfolioStressScenarioPipeline') as MockPipelineClass, \
             patch('skills.market_portfolio_stress_backtest_aggregator.PortfolioScenarioSimulator') as MockSimulatorClass:

            instance_pipeline = MockPipelineClass.return_value
            instance_pipeline.execute.return_value = mock_pipeline_result

            instance_simulator = MockSimulatorClass.return_value
            instance_simulator.run_stress_test.return_value = mock_simulator_result

            aggregator = MarketPortfolioStressBacktestAggregator(self.storage_file)
            report = aggregator.generate_report(self.symbol, self.percentage, self.shifts)

            MockPipelineClass.assert_called_once_with(self.storage_file)
            MockSimulatorClass.assert_called_once_with(self.storage_file)

            instance_pipeline.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            instance_simulator.run_stress_test.assert_called_once_with(self.symbol, self.shifts)

            self.assertIn("pipeline_data", report)
            self.assertIn("simulation_data", report)
            self.assertIn("aggregated_at", report)
            self.assertEqual(report["pipeline_data"], mock_pipeline_result)
            self.assertEqual(report["simulation_data"], mock_simulator_result)

    def test_functional_aggregator_helper(self):
        mock_pipeline_res = {
            "exec_id": uuid.uuid4().hex,
            "target": self.symbol
        }
        mock_simulator_res = {
            "sim_id": uuid.uuid4().hex,
            "score": random.randint(1, 100)
        }

        with patch('skills.market_portfolio_stress_backtest_aggregator.run_stress_scenario_pipeline') as mock_run_pipe, \
             patch('skills.market_portfolio_stress_backtest_aggregator.simulate_market_scenario') as mock_sim_market:

            mock_run_pipe.return_value = mock_pipeline_res
            mock_sim_market.return_value = mock_simulator_res

            result = aggregate_stress_backtest_report(self.storage_file, self.symbol, self.percentage, self.shifts)

            mock_run_pipe.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_sim_market.assert_called_once_with(self.storage_file, self.symbol, self.percentage)

            self.assertEqual(result["stress_pipeline"], mock_pipeline_res)
            self.assertEqual(result["market_simulation"], mock_simulator_res)
            self.assertEqual(result["symbol"], self.symbol)

    def test_aggregator_handles_exceptions_gracefully(self):
        random_error_msg = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_backtest_aggregator.PortfolioStressScenarioPipeline') as MockPipelineClass:
            instance_pipeline = MockPipelineClass.return_value
            instance_pipeline.execute.side_effect = Exception(random_error_msg)

            aggregator = MarketPortfolioStressBacktestAggregator(self.storage_file)

            with self.assertRaises(Exception) as ctx:
                aggregator.generate_report(self.symbol, self.percentage, self.shifts)

            self.assertIn(random_error_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()