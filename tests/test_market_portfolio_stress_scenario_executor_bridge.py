import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_stress_scenario_executor_bridge import (
    PortfolioStressScenarioExecutorBridge,
    execute_stress_execution_bridge
)

class TestPortfolioStressScenarioExecutorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(2, 5))]
        
        self.pipeline_expected_result = {"pipeline_id": uuid.uuid4().hex, "status": "success"}
        self.simulation_expected_result = {"simulation_id": uuid.uuid4().hex, "risk_score": random.random()}

    def test_execute_stress_workflow(self):
        with patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_class, \
             patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioScenarioSimulator") as mock_simulator_class:
            
            mock_pipeline_instance = mock_pipeline_class.return_value
            mock_pipeline_instance.execute.return_value = self.pipeline_expected_result

            mock_simulator_instance = mock_simulator_class.return_value
            mock_simulator_instance.run_stress_test.return_value = self.simulation_expected_result

            bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
            result = bridge.execute_stress_workflow(self.symbol, self.percentage, self.shifts)

            mock_pipeline_class.assert_called_once_with(self.storage_file)
            mock_simulator_class.assert_called_once_with(self.storage_file)

            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_simulator_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)

            self.assertIn("pipeline_report", result)
            self.assertIn("simulation_report", result)
            self.assertEqual(result["pipeline_report"], self.pipeline_expected_result)
            self.assertEqual(result["simulation_report"], self.simulation_expected_result)

    def test_execute_stress_test_workflow(self):
        with patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_class, \
             patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioScenarioSimulator") as mock_simulator_class:
            
            mock_pipeline_instance = mock_pipeline_class.return_value
            mock_pipeline_instance.execute.return_value = self.pipeline_expected_result

            mock_simulator_instance = mock_simulator_class.return_value
            mock_simulator_instance.run_stress_test.return_value = self.simulation_expected_result

            bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
            result = bridge.execute_stress_test_workflow(self.symbol, self.percentage, self.shifts)

            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_simulator_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)

            self.assertIn("pipeline_result", result)
            self.assertIn("simulation_result", result)
            self.assertEqual(result["pipeline_result"], self.pipeline_expected_result)
            self.assertEqual(result["simulation_result"], self.simulation_expected_result)

    def test_execute_stress_execution_bridge_functional(self):
        with patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_class, \
             patch("skills.market_portfolio_stress_scenario_executor_bridge.PortfolioScenarioSimulator") as mock_simulator_class:
            
            mock_pipeline_instance = mock_pipeline_class.return_value
            mock_pipeline_instance.execute.return_value = self.pipeline_expected_result

            mock_simulator_instance = mock_simulator_class.return_value
            mock_simulator_instance.run_stress_test.return_value = self.simulation_expected_result

            result = execute_stress_execution_bridge(self.storage_file, self.symbol, self.percentage, self.shifts)

            mock_pipeline_class.assert_called_once_with(self.storage_file)
            mock_simulator_class.assert_called_once_with(self.storage_file)
            
            self.assertEqual(result["pipeline_report"], self.pipeline_expected_result)
            self.assertEqual(result["simulation_report"], self.simulation_expected_result)

if __name__ == "__main__":
    unittest.main()