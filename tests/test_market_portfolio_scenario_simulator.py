import unittest
from unittest.mock import patch, mock_open
import json
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
        self.current_price = round(random.uniform(10.0, 1000.0), 2)
        self.quantity = round(random.uniform(1.0, 100.0), 2)
        self.percentage = round(random.uniform(-50.0, 50.0), 2)

    def test_load_data_success(self):
        mock_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        json_content = json.dumps(mock_data)
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch("builtins.open", mock_open(read_data=json_content)):
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, mock_data)

    def test_load_data_io_error(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch("builtins.open", side_effect=IOError):
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_load_data_json_decode_error(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch("builtins.open", mock_open(read_data=uuid.uuid4().hex)):
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_simulate_scenario_direct_key(self):
        mock_data = {
            self.symbol: {
                "price": self.current_price,
                "shares": self.quantity
            }
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            
            expected_simulated_price = self.current_price * (1 + self.percentage / 100.0)
            expected_pnl = (expected_simulated_price - self.current_price) * self.quantity
            
            self.assertEqual(result["symbol"], self.symbol)
            self.assertAlmostEqual(result["simulated_price"], expected_simulated_price)
            self.assertAlmostEqual(result["pnl_impact"], expected_pnl)
            self.assertAlmostEqual(result["portfolio_value_delta"], expected_pnl)

    def test_simulate_scenario_assets_list(self):
        mock_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_holdings_list(self):
        mock_data = {
            "holdings": [
                {
                    "symbol": self.symbol,
                    "price": self.current_price,
                    "shares": self.quantity
                }
            ]
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_root_dict(self):
        mock_data = {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "quantity": self.quantity
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_list_root(self):
        mock_data = [
            {
                "symbol": self.symbol,
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        ]
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            result = simulator.simulate_scenario(self.symbol, self.percentage)
            self.assertEqual(result["symbol"], self.symbol)

    def test_simulate_scenario_symbol_not_found(self):
        mock_data = {
            f"OTHER_{uuid.uuid4().hex[:4]}": {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            with self.assertRaises(KeyError):
                simulator.simulate_scenario(self.symbol, self.percentage)

    def test_run_stress_test(self):
        shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]
        mock_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value=mock_data):
            report = simulator.run_stress_test(self.symbol, shifts)
            
            self.assertEqual(len(report), len(shifts))
            for i, item in enumerate(report):
                self.assertEqual(item["shift_percentage"], shifts[i])
                expected_price = self.current_price * (1 + shifts[i] / 100.0)
                self.assertAlmostEqual(item["resulting_valuation"], expected_price)

    def test_run_stress_test_with_exception(self):
        shifts = [random.randint(1, 10)]
        simulator = PortfolioScenarioSimulator(self.storage_file)
        
        with patch.object(simulator, "load_data", return_value={}):
            report = simulator.run_stress_test(self.symbol, shifts)
            
            self.assertEqual(len(report), len(shifts))
            self.assertEqual(report[0]["resulting_valuation"], 0.0)

    def test_simulate_market_scenario_helper(self):
        mock_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=mock_data):
            res = simulate_market_scenario(self.storage_file, self.symbol, self.percentage)
            self.assertEqual(res["symbol"], self.symbol)

    def test_run_stress_test_helper(self):
        range_min = random.randint(-5, -1)
        range_max = random.randint(1, 5)
        step = 1
        
        mock_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        
        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=mock_data):
            result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
            
            self.assertEqual(result["symbol"], self.symbol)
            expected_shifts_count = len(list(range(range_min, range_max + 1, step)))
            self.assertEqual(len(result["scenarios"]), expected_shifts_count)


if __name__ == "__main__":
    unittest.main()