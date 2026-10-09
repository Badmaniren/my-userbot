import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_executor_bridge import (
    PortfolioStressScenarioExecutorBridge,
    execute_stress_execution_bridge
)

class TestPortfolioStressScenarioExecutorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_stress_storage_{uuid.uuid4()}.db"
        self.bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(5.0, 35.0), 2)
        self.shifts = [round(random.uniform(-0.2, -0.05), 4), round(random.uniform(0.05, 0.2), 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_execute_stress_workflow_integration(self):
        result = self.bridge.execute_stress_workflow(self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("pipeline_report", result)
        self.assertIn("simulation_report", result)
        
        self.assertIsInstance(result["pipeline_report"], dict)
        self.assertIsInstance(result["simulation_report"], dict)

    def test_execute_stress_test_workflow_integration(self):
        result = self.bridge.execute_stress_test_workflow(self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("pipeline_result", result)
        self.assertIn("simulation_result", result)
        
        self.assertIsInstance(result["pipeline_result"], dict)
        self.assertIsInstance(result["simulation_result"], dict)

    def test_execute_stress_execution_bridge_functional(self):
        result = execute_stress_execution_bridge(self.storage_file, self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("pipeline_report", result)
        self.assertIn("simulation_report", result)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file should be initialized and used by pipeline and simulator.")

if __name__ == "__main__":
    unittest.main()