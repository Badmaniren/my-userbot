import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_slippage_model import calculate_slippage

class TestPortfolioScenarioSimulatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)
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

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_simulate_scenario_with_slippage_model(self):
        percentage = round(random.uniform(-20.0, 20.0), 2)
        slippage_factor = round(random.uniform(0.1, 2.0), 2)

        calculated_slippage = calculate_slippage(self.initial_price, slippage_factor)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, percentage, slippage_factor=slippage_factor)
        
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("simulated_price", result)
        self.assertIn("pnl_impact", result)
        self.assertIn("portfolio_value_delta", result)
        
        base_price = self.initial_price * (1 + percentage / 100.0)
        expected_price = base_price + (base_price * slippage_factor / 100.0)
        self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)

    def test_integration_wrapper_functions_and_valuation(self):
        percentage = round(random.uniform(1.0, 15.0), 2)

        wrapper_result = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        self.assertEqual(wrapper_result["symbol"], self.symbol)

        valuation_tool = PortfolioValuation()
        self.assertIsNotNone(valuation_tool)

        parser_tool = MarketParser()
        self.assertIsNotNone(parser_tool)

    def test_integration_stress_test_pipeline(self):
        min_shift = random.randint(-10, -5)
        max_shift = random.randint(5, 10)
        step = random.randint(1, 3)

        stress_result = run_stress_test(self.storage_file, self.symbol, min_shift, max_shift, step)
        
        self.assertEqual(stress_result["symbol"], self.symbol)
        self.assertIsInstance(stress_result["scenarios"], list)
        self.assertGreater(len(stress_result["scenarios"]), 0)
        
        for scenario in stress_result["scenarios"]:
            self.assertIn("shift_percentage", scenario)
            self.assertIn("resulting_valuation", scenario)

if __name__ == "__main__":
    unittest.main()