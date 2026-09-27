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
        
        self.symbol = f"TICK_{random.randint(100, 999)}"
        self.current_price = round(random.uniform(10.0, 500.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 4)
        
        self.test_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_simulate_market_scenario_integration(self):
        percentage = round(random.uniform(-50.0, 50.0), 2)
        
        parser = MarketParser()
        valuation = PortfolioValuation()
        
        result = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        expected_pnl = (expected_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_run_stress_test_integration(self):
        range_min = -10
        range_max = 10
        step = 5
        
        stress_result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        
        scenarios = stress_result["scenarios"]
        self.assertGreater(len(scenarios), 0)
        
        for scenario in scenarios:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)
            self.assertIsInstance(scenario["shift_percentage"], float)
            self.assertIsInstance(scenario["resulting_valuation"], float)

    def test_simulator_class_exceptions_and_validation(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        invalid_symbol = f"BAD_{uuid.uuid4().hex}"
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(invalid_symbol, 10.0)

if __name__ == '__main__':
    unittest.main()