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
        self.current_price = round(random.uniform(10.0, 1000.0), 4)
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

    def tearDown(s):
        if os.path.exists(s.storage_file):
            os.remove(s.storage_file)
        if os.path.exists(s.test_dir):
            os.rmdir(s.test_dir)

    def test_simulate_scenario_integration(self):
        percentage = round(random.uniform(-50.0, 50.0), 2)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        expected_pnl = (expected_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_wrapper_functions_integration(self):
        percentage = round(random.uniform(-20.0, 20.0), 2)
        
        res_wrapper = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        self.assertIsInstance(res_wrapper, dict)
        self.assertEqual(res_wrapper["symbol"], self.symbol)
        
        stress_res = run_stress_test(self.storage_file, self.symbol, -10, 10, 5)
        self.assertIsInstance(stress_res, dict)
        self.assertEqual(stress_res["symbol"], self.symbol)
        self.assertIn("scenarios", stress_res)
        self.assertIsInstance(stress_res["scenarios"], list)
        self.assertGreater(len(stress_res["scenarios"]), 0)

if __name__ == "__main__":
    unittest.main()