import unittest
from unittest.mock import patch, mock_open
import json
import os
import uuid
import random
import io

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)


class TestPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.current_price = round(random.uniform(10.0, 1000.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 2)

    def test_load_data_success(self):
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        mock_file_content = json.dumps(test_data)
        
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, test_data)

    def test_load_data_io_error(self):
        with patch("builtins.open", side_effect=IOError):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_load_data_json_decode_error(self):
        invalid_json = f"INVALID_JSON_{uuid.uuid4().hex}"
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_simulate_scenario_dict_root_symbol(self):
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            
            expected_price = self.current_price * (1 + self.percentage / 100.0)
            expected_pnl = (expected_price - self.current_price) * self.quantity
            
            self.assertEqual(result["symbol"], self.symbol)
            self.assertAlmostEqual(result["simulated_price"], expected_price)
            self.assertAlmostEqual(result["pnl_impact"], expected_pnl)

    def test_simulate_scenario_assets_list(self):
        test_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "price": self.current_price,
                    "shares": self.quantity
                }
            ]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            
            expected_price = self.current_price * (1 + self.percentage / 100.0)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertAlmostEqual(result["simulated_price"], expected_price)

    def test_simulate_scenario_holdings_list(self):
        test_data = {
            "holdings": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_list_root(self):
        test_data = [
            {
                "symbol": self.symbol,
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        ]
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_not_found(self):
        missing_symbol = f"MISSING_{uuid.uuid4().hex[:6]}"
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            with self.assertRaises(KeyError):
                simulator.simulate_scenario(missing_symbol, self.percentage)

    def test_run_stress_test(self):
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            report = simulator.run_stress_test(self.symbol, shifts)
            
            self.assertEqual(len(report), len(shifts))
            for i, item in enumerate(report):
                self.assertEqual(item["shift_percentage"], shifts[i])
                expected_valuation = self.current_price * (1 + shifts[i] / 100.0)
                self.assertAlmostEqual(item["resulting_valuation"], expected_valuation)

    def test_run_stress_test_with_exception(self):
        missing_symbol = f"MISSING_{uuid.uuid4().hex[:6]}"
        test_data = {}
        shifts = [random.randint(1, 5)]
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            report = simulator.run_stress_test(missing_symbol, shifts)
            
            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]["resulting_valuation"], 0.0)

    def test_simulate_market_scenario_wrapper(self):
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            result = simulate_market_scenario(self.storage_file, self.symbol, self.percentage)
            self.assertEqual(result["symbol"], self.symbol)

    def test_run_stress_test_wrapper(self):
        test_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        range_min = random.randint(-5, -2)
        range_max = random.randint(2, 5)
        step = 1
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertIsInstance(result["scenarios"], list)
            self.assertTrue(len(result["scenarios"]) > 0)


if __name__ == "__main__":
    unittest.main()