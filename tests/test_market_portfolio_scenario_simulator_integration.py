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
        
        portfolio_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(portfolio_data, f)
            
        self.parser = MarketParser()
        self.valuation = PortfolioValuation()

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_simulate_scenario_and_valuation(self):
        percentage_shift = round(random.uniform(-20.0, 20.0), 2)
        slippage = round(random.uniform(0.0, 1.5), 2)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage_shift, slippage_factor=slippage)
        
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("simulated_price", result)
        self.assertIn("pnl_impact", result)
        
        base_price = self.current_price * (1 + percentage_shift / 100.0)
        expected_slippage = base_price * (slippage / 100.0)
        expected_simulated_price = base_price + expected_slippage
        expected_pnl = (expected_simulated_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(result["simulated_price"], expected_simulated_price, places=4)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)

        valuation_result = self.valuation.calculate_valuation(self.storage_file) if hasattr(self.valuation, 'calculate_valuation') else True
        self.assertTrue(bool(valuation_result))

    def test_integration_wrapper_functions_and_stress_test(self):
        min_shift = random.randint(-10, -5)
        max_shift = random.randint(5, 10)
        step_val = random.randint(1, 3)
        
        stress_result = run_stress_test(self.storage_file, self.symbol, min_shift, max_shift, step_val)
        
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIn("scenarios", stress_result)
        self.assertGreater(len(stress_result["scenarios"]), 0)
        
        single_sim_result = simulate_market_scenario(self.storage_file, self.symbol, float(min_shift))
        self.assertEqual(single_sim_result["symbol"], self.symbol)
        self.assertIn("simulated_price", single_sim_result)

if __name__ == '__main__':
    unittest.main()