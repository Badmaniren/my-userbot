import unittest
import json
import os
import uuid
import random
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.current_price = round(random.uniform(10.0, 1000.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 2)
        
        self.portfolio_data = {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "quantity": self.quantity
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(self.portfolio_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_simulate_market_scenario_integration(self):
        percentage = round(random.uniform(-50.0, 50.0), 2)
        result = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        expected_pnl = (expected_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_run_stress_test_integration(self):
        range_min = random.randint(-20, -5)
        range_max = random.randint(5, 20)
        step = random.randint(1, 5)
        
        stress_result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        
        scenarios = stress_result["scenarios"]
        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)
        
        for scenario in scenarios:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)
            self.assertIsInstance(scenario["shift_percentage"], (int, float))
            self.assertIsInstance(scenario["resulting_valuation"], (int, float))

    def test_simulator_class_missing_symbol(self):
        missing_symbol = f"MISSING_{uuid.uuid4().hex[:6].upper()}"
        simulator = PortfolioScenarioSimulator(self.storage_file)
        percentage = float(random.randint(1, 10))
        
        with self.assertRaises((KeyError, ValueError, TypeError)):
            simulator.simulate_scenario(missing_symbol, percentage)

if __name__ == '__main__':
    unittest.main()