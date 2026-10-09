import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_executor_bridge import PortfolioStressScenarioExecutorBridge
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class TestMarketPortfolioStressScenarioExecutorBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.json"
        
        with open(self.storage_file, "w") as f:
            f.write('{"initial": "data"}')

        self.bridge = PortfolioStressScenarioExecutorBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_executor_bridge_integration(self):
        symbol = f"SYM_{random.randint(1000, 9999)}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

        result = self.bridge.execute_stress_test_workflow(symbol=symbol, percentage=percentage, shifts=shifts)

        self.assertIsNotNone(result)
        self.assertIn("pipeline_result", result)
        self.assertIn("simulation_result", result)

if __name__ == "__main__":
    unittest.main()