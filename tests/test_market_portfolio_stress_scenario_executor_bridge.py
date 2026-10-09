import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_scenario_executor_bridge import (
    PortfolioStressScenarioExecutorBridge,
    execute_stress_execution_bridge
)


class TestPortfolioStressScenarioExecutorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(2, 5))]
        self.mock_pipeline_result = {
            "status": "success",
            "symbol": self.symbol,
            "percentage": self.percentage,
            "shifts": self.shifts,
            "pipeline_id": uuid.uuid4().hex
        }
        self.mock_simulator_result = {
            "simulation_executed": True,
            "symbol": self.symbol,
            "results": [{"shift": s, "value": random.uniform(100.0, 1000.0)} for s in self.shifts]
        }

    def test_executor_bridge_initialization(self):
        bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
        self.assertEqual(bridge.storage_file, self.storage_file)
        self.assertIsNotNone(bridge.pipeline)
        self.assertIsNotNone(bridge.simulator)

    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline.execute')
    @patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test')
    def test_execute_stress_workflow_success(self, mock_run_stress_test, mock_pipeline_execute):
        mock_pipeline_execute.return_value = self.mock_pipeline_result
        mock_run_stress_test.return_value = self.mock_simulator_result

        bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
        combined_result = bridge.execute_stress_workflow(self.symbol, self.percentage, self.shifts)

        self.assertIn("pipeline_report", combined_result)
        self.assertIn("simulation_report", combined_result)
        self.assertEqual(combined_result["pipeline_report"]["symbol"], self.symbol)
        self.assertEqual(combined_result["simulation_report"]["symbol"], self.symbol)
        
        mock_pipeline_execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
        mock_run_stress_test.assert_called_once_with(self.symbol, self.shifts)

    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline.execute')
    def test_execute_stress_workflow_pipeline_failure(self, mock_pipeline_execute):
        mock_pipeline_execute.side_effect = RuntimeError(uuid.uuid4().hex)

        bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
        with self.assertRaises(RuntimeError):
            bridge.execute_stress_workflow(self.symbol, self.percentage, self.shifts)

    @patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test')
    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline.execute')
    def test_global_execution_function(self, mock_pipeline_execute, mock_run_stress_test):
        mock_pipeline_execute.return_value = self.mock_pipeline_result
        mock_run_stress_test.return_value = self.mock_simulator_result

        result = execute_stress_execution_bridge(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["pipeline_report"]["percentage"], self.percentage)
        self.assertEqual(result["simulation_report"]["symbol"], self.symbol)


if __name__ == '__main__':
    unittest.main()