import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")

        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.current_price = round(random.uniform(10.0, 500.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 4)
        
        self.portfolio_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(self.portfolio_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_simulate_scenario_integration(self):
        percentage = round(random.uniform(-20.0, 20.0), 2)
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_simulated_price = self.current_price * (1 + percentage / 100.0)
        self.assertAlmostEqual(result["simulated_price"], expected_simulated_price, places=3)
        self.assertIn("pnl_impact", result)
        self.assertIn("portfolio_value_delta", result)

    def test_simulate_market_scenario_wrapper(self):
        percentage = round(random.uniform(-10.0, 10.0), 2)
        result = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("simulated_price", result)

    def test_run_stress_test_integration(self):
        range_min = random.randint(-10, -1)
        range_max = random.randint(1, 10)
        step = random.randint(1, 2)
        
        stress_result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        self.assertIsInstance(stress_result["scenarios"], list)
        self.assertGreater(len(stress_result["scenarios"]), 0)
        
        for scenario in stress_result["scenarios"]:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)

    def test_simulate_scenario_invalid_symbol(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        invalid_symbol = f"BAD_{uuid.uuid4().hex}"
        percentage = round(random.uniform(1.0, 5.0), 2)
        
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(invalid_symbol, percentage)

if __name__ == "__main__":
    unittest.main()