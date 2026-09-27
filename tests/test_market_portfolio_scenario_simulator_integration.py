import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
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

    def test_simulate_market_scenario_integration(self):
        percentage_shift = round(random.uniform(-50.0, 50.0), 2)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage_shift)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_price = self.current_price * (1 + percentage_shift / 100.0)
        expected_pnl = (expected_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)

        wrapper_result = simulate_market_scenario(self.storage_file, self.symbol, percentage_shift)
        self.assertEqual(wrapper_result["symbol"], self.symbol)
        self.assertAlmostEqual(wrapper_result["simulated_price"], expected_price, places=4)

    def test_run_stress_test_integration(self):
        min_val = random.randint(-20, -10)
        max_val = random.randint(10, 20)
        step_val = random.randint(5, 10)
        
        stress_result = run_stress_test(self.storage_file, self.symbol, min_val, max_val, step_val)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        self.assertIsInstance(stress_result["scenarios"], list)
        self.assertGreater(len(stress_result["scenarios"]), 0)
        
        for scenario in stress_result["scenarios"]:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)
            self.assertIsInstance(scenario["shift_percentage"], (int, float))
            self.assertIsInstance(scenario["resulting_valuation"], (int, float))

    def test_invalid_symbol_raises_error(self):
        invalid_symbol = f"BAD_{uuid.uuid4().hex}"
        percentage_shift = round(random.uniform(-10.0, 10.0), 2)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(invalid_symbol, percentage_shift)

if __name__ == '__main__':
    unittest.main()