import unittest
import os
import json
import uuid
import random
from skills.db_storage import save_portfolio, load_portfolio
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data_integration"
        os.makedirs(self.test_dir, exist_ok=True)
        self.filename = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")

        self.symbol = f"TST_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 4)
        
        self.portfolio_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.price,
                    "quantity": self.quantity
                }
            ]
        }
        save_portfolio(self.portfolio_data, self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_simulate_market_scenario_integration(self):
        percentage_shift = round(random.uniform(-50.0, 50.0), 2)

        result = simulate_market_scenario(self.filename, self.symbol, percentage_shift)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_simulated_price = self.price * (1 + percentage_shift / 100.0)
        expected_pnl = (expected_simulated_price - self.price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_simulated_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_run_stress_test_integration(self):
        range_min = random.randint(-20, -10)
        range_max = random.randint(10, 20)
        step = random.choice([5, 10])
        
        stress_result = run_stress_test(self.filename, self.symbol, range_min, range_max, step)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        
        scenarios = stress_result["scenarios"]
        self.assertIsInstance(scenarios, list)
        self.assertTrue(len(scenarios) > 0)
        
        for scenario in scenarios:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)
            shift = scenario["shift_percentage"]
            expected_val = self.price * (1 + shift / 100.0)
            self.assertAlmostEqual(scenario["resulting_valuation"], expected_val, places=4)

    def test_simulator_class_direct_integration(self):
        simulator = PortfolioScenarioSimulator(self.filename)
        loaded = simulator.load_data(self.filename)
        self.assertIsInstance(loaded, dict)
        self.assertIn("assets", loaded)
        
        invalid_symbol = f"INV_{uuid.uuid4().hex}"
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(invalid_symbol, 10.0)

if __name__ == '__main__':
    unittest.main()