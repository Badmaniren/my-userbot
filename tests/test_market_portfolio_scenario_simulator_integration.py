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
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.unique_id = uuid.uuid4().hex[:8]
        self.storage_filename = f"test_portfolio_{self.unique_id}.json"
        self.storage_file = os.path.join(self.test_dir, self.storage_filename)
        
        self.symbol = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        self.initial_price = round(random.uniform(10.0, 1000.0), 4)
        self.quantity = round(random.uniform(1.0, 100.0), 2)
        
        self.portfolio_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.initial_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(self.portfolio_data, f)

    def tearDown(s):
        if os.path.exists(s.storage_file):
            try:
                os.remove(s.storage_file)
            except OSError:
                pass

    def test_simulate_scenario_integration_without_mocks(self):
        percentage_shift = round(random.uniform(-20.0, 20.0), 2)
        slippage = round(random.uniform(0.0, 2.0), 2)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage_shift, slippage_factor=slippage)
        
        self.assertEqual(result["symbol"], self.symbol)
        
        expected_base = self.initial_price * (1 + percentage_shift / 100.0)
        expected_slippage_adj = expected_base * (slippage / 100.0)
        expected_price = expected_base + expected_slippage_adj
        expected_pnl = (expected_price - self.initial_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)
        self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl, places=4)

    def test_wrapper_functions_integration(self):
        percentage_shift = round(random.uniform(-10.0, 10.0), 2)
        
        wrapper_result = simulate_market_scenario(self.storage_file, self.symbol, percentage_shift)
        self.assertEqual(wrapper_result["symbol"], self.symbol)
        self.assertIn("simulated_price", wrapper_result)
        
        stress_result = run_stress_test(self.storage_file, self.symbol, -5, 5, 5)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIsInstance(stress_result["scenarios"], list)
        self.assertGreaterEqual(len(stress_result["scenarios"]), 1)
        
        for scenario in stress_result["scenarios"]:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)

if __name__ == '__main__':
    unittest.main()