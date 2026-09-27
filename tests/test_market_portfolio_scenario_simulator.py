import unittest
from unittest.mock import patch, mock_open
import json
import io
import uuid
import random
import string

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)

class TestPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.simulator = PortfolioScenarioSimulator(self.storage_file)

    def test_load_data_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 9999)
        mock_data = json.dumps({rand_key: rand_val})
        
        with patch('builtins.open', mock_open(read_data=mock_data)):
            data = self.simulator.load_data(self.storage_file)
            self.assertIn(rand_key, data)
            self.assertEqual(data[rand_key], rand_val)

    def test_load_data_failure(self):
        rand_corrupt = ''.join(random.choices(string.ascii_letters, k=20))
        with patch('builtins.open', mock_open(read_data=rand_corrupt)):
            data = self.simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_simulate_scenario_dict_root(self):
        symbol = uuid.uuid4().hex[:6].upper()
        price = round(random.uniform(10.0, 500.0), 2)
        quantity = round(random.uniform(1.0, 50.0), 2)
        percentage = round(random.uniform(-20.0, 20.0), 2)

        portfolio = {
            symbol: {
                "current_price": price,
                "quantity": quantity
            }
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio):
            res = self.simulator.simulate_scenario(symbol, percentage)
            
            expected_price = price * (1 + percentage / 100.0)
            expected_pnl = (expected_price - price) * quantity
            
            self.assertEqual(res["symbol"], symbol)
            self.assertAlmostEqual(res["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=4)

    def test_simulate_scenario_assets_list(self):
        symbol = uuid.uuid4().hex[:6].upper()
        price = round(random.uniform(1.0, 100.0), 2)
        shares = round(random.uniform(10.0, 1000.0), 2)
        percentage = round(random.uniform(1.0, 15.0), 2)

        portfolio = {
            "assets": [
                {
                    "symbol": symbol,
                    "price": price,
                    "shares": shares
                }
            ]
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio):
            res = self.simulator.simulate_scenario(symbol, str(percentage))
            
            expected_price = price * (1 + percentage / 100.0)
            expected_pnl = (expected_price - price) * shares
            
            self.assertEqual(res["symbol"], symbol)
            self.assertAlmostEqual(res["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=4)

    def test_simulate_scenario_invalid_symbol_type(self):
        invalid_symbols = [None, 12345, "", "   ", []]
        for sym in invalid_symbols:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(sym, 10.0)

    def test_simulate_scenario_invalid_percentage(self):
        symbol = uuid.uuid4().hex[:6].upper()
        invalid_percentages = ["abc", None, {}]
        portfolio = {symbol: {"current_price": 10.0, "quantity": 1.0}}
        
        with patch.object(self.simulator, 'load_data', return_value=portfolio):
            for pct in invalid_percentages:
                with self.assertRaises(ValueError):
                    self.simulator.simulate_scenario(symbol, pct)

    def test_simulate_scenario_symbol_not_found(self):
        symbol = uuid.uuid4().hex[:6].upper()
        missing_symbol = uuid.uuid4().hex[:6].upper()
        portfolio = {symbol: {"current_price": 10.0, "quantity": 1.0}}

        with patch.object(self.simulator, 'load_data', return_value=portfolio):
            with self.assertRaises(KeyError):
                self.simulator.simulate_scenario(missing_symbol, 5.0)

    def test_run_stress_test(self):
        symbol = uuid.uuid4().hex[:6].upper()
        price = 100.0
        quantity = 10.0
        shifts = [-10, 0, 10]

        portfolio = {
            symbol: {
                "current_price": price,
                "quantity": quantity
            }
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio):
            report = self.simulator.run_stress_test(symbol, shifts)
            self.assertEqual(len(report), 3)
            self.assertEqual(report[0]["shift_percentage"], -10)
            self.assertAlmostEqual(report[0]["resulting_valuation"], 90.0)
            self.assertEqual(report[1]["shift_percentage"], 0)
            self.assertAlmostEqual(report[1]["resulting_valuation"], 100.0)
            self.assertEqual(report[2]["shift_percentage"], 10)
            self.assertAlmostEqual(report[2]["resulting_valuation"], 110.0)

    def test_wrapper_simulate_market_scenario(self):
        symbol = uuid.uuid4().hex[:6].upper()
        percentage = 5.0
        mock_result = {
            "symbol": symbol,
            "simulated_price": 105.0,
            "pnl_impact": 50.0,
            "portfolio_value_delta": 50.0
        }

        with patch.object(PortfolioScenarioSimulator, 'simulate_scenario', return_value=mock_result) as mock_sim:
            res = simulate_market_scenario(self.storage_file, symbol, percentage)
            mock_sim.assert_called_once_with(symbol, percentage)
            self.assertEqual(res, mock_result)

    def test_wrapper_run_stress_test(self):
        symbol = uuid.uuid4().hex[:6].upper()
        range_min = 0
        range_max = 10
        step = 5

        mock_scenarios = [
            {"shift_percentage": 0, "resulting_valuation": 100.0},
            {"shift_percentage": 5, "resulting_valuation": 105.0},
            {"shift_percentage": 10, "resulting_valuation": 110.0}
        ]

        with patch.object(PortfolioScenarioSimulator, 'run_stress_test', return_value=mock_scenarios) as mock_stress:
            res = run_stress_test(self.storage_file, symbol, range_min, range_max, step)
            mock_stress.assert_called_once_with(symbol, [0.0, 5.0, 10.0])
            self.assertEqual(res["symbol"], symbol)
            self.assertEqual(res["scenarios"], mock_scenarios)

if __name__ == '__main__':
    unittest.main()