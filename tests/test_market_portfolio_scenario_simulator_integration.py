import unittest
import json
import os
import tempfile
import uuid
import random

from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 2)
        self.percentage = round(random.uniform(-20.0, 20.0), 2)
        
        self.portfolio_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.price,
                    "quantity": self.quantity
                }
            ]
        }
        
        self.fd, self.temp_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(self.fd, 'w') as f:
            json.dump(self.portfolio_data, f)
            
    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)
            
    def test_simulate_market_scenario_integration(self):
        result = simulate_market_scenario(self.temp_path, self.symbol, self.percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_price = self.price * (1 + self.percentage / 100.0)
        expected_pnl = (expected_price - self.price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_run_stress_test_integration(self):
        range_min = -10
        range_max = 10
        step = 5
        
        stress_result = run_stress_test(self.temp_path, self.symbol, range_min, range_max, step)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        
        scenarios = stress_result["scenarios"]
        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)
        
        for item in scenarios:
            self.assertIn("shift_percentage", item)
            self.assertIn("resulting_valuation", item)
            self.assertIsInstance(item["shift_percentage"], float)
            self.assertIsInstance(item["resulting_valuation"], float)

    def test_class_methods_and_error_handling(self):
        simulator = PortfolioScenarioSimulator(self.temp_path)
        
        with self.assertRaises(ValueError):
            simulator.simulate_scenario("", self.percentage)
            
        with self.assertRaises(ValueError):
            simulator.simulate_scenario(self.symbol, "not_a_number")
            
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(f"NONEXISTENT_{uuid.uuid4().hex[:4]}", self.percentage)

if __name__ == '__main__':
    unittest.main()