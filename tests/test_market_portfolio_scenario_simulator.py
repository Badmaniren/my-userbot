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
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.simulator = PortfolioScenarioSimulator(self.random_storage)

    def test_load_data_success(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        rand_shares = round(random.uniform(1.0, 500.0), 2)
        
        mock_data = {
            rand_symbol: {
                "current_price": rand_price,
                "quantity": rand_shares
            }
        }
        mock_json_str = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=mock_json_str)):
            data = self.simulator.load_data(self.random_storage)
            self.assertIn(rand_symbol, data)
            self.assertEqual(data[rand_symbol]["current_price"], rand_price)

    def test_load_data_io_error(self):
        with patch("builtins.open", side_effect=IOError("Disk explosion")):
            data = self.simulator.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_load_data_json_decode_error(self):
        corrupted_data = "CORRUPTED_RANDOM_GARBAGE_" + uuid.uuid4().hex
        with patch("builtins.open", mock_open(read_data=corrupted_data)):
            data = self.simulator.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_simulate_scenario_valid_dict_root(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5].upper()}"
        price = round(random.uniform(50.0, 500.0), 2)
        quantity = round(random.uniform(10.0, 100.0), 2)
        percentage = round(random.uniform(-20.0, 20.0), 2)

        portfolio_data = {
            rand_symbol: {
                "price": price,
                "shares": quantity
            }
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            result = self.simulator.simulate_scenario(rand_symbol, percentage)
            
            expected_price = price * (1 + percentage / 100.0)
            expected_pnl = (expected_price - price) * quantity

            self.assertEqual(result["symbol"], rand_symbol)
            self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)

    def test_simulate_scenario_assets_list(self):
        rand_symbol = f"ASSET_{uuid.uuid4().hex[:4].upper()}"
        price = round(random.uniform(1.0, 100.0), 2)
        quantity = round(random.uniform(5.0, 50.0), 2)
        percentage = 15.5

        portfolio_data = {
            "assets": [
                {"symbol": "WRONG_SYMBOL", "current_price": 10.0, "quantity": 1.0},
                {"symbol": rand_symbol, "current_price": price, "quantity": quantity}
            ]
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            result = self.simulator.simulate_scenario(rand_symbol, percentage)
            self.assertEqual(result["symbol"], rand_symbol)
            expected_price = price * (1 + percentage / 100.0)
            self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)

    def test_simulate_scenario_holdings_list(self):
        rand_symbol = f"HOLD_{uuid.uuid4().hex[:4].upper()}"
        price = round(random.uniform(5.0, 200.0), 2)
        quantity = round(random.uniform(2.0, 20.0), 2)
        percentage = -10.0

        portfolio_data = {
            "holdings": [
                {"symbol": rand_symbol, "current_price": price, "quantity": quantity}
            ]
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            result = self.simulator.simulate_scenario(rand_symbol, percentage)
            self.assertEqual(result["symbol"], rand_symbol)
            expected_price = price * (1 + percentage / 100.0)
            self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)

    def test_simulate_scenario_list_root(self):
        rand_symbol = f"LST_{uuid.uuid4().hex[:4].upper()}"
        price = round(random.uniform(10.0, 50.0), 2)
        quantity = round(random.uniform(1.0, 10.0), 2)
        percentage = 5.0

        portfolio_data = [
            {"symbol": rand_symbol, "current_price": price, "quantity": quantity}
        ]

        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            result = self.simulator.simulate_scenario(rand_symbol, percentage)
            self.assertEqual(result["symbol"], rand_symbol)
            self.assertAlmostEqual(result["pnl_impact"], (price * 0.05) * quantity, places=4)

    def test_simulate_scenario_invalid_symbol_raises_value_error(self):
        invalid_symbols = ["", "   ", None, 12345]
        for inv_sym in invalid_symbols:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(inv_sym, 10.0)

    def test_simulate_scenario_invalid_percentage_raises_value_error(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:4]}"
        invalid_percentages = ["not_a_float", {}, []]
        for inv_pct in invalid_percentages:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(rand_symbol, inv_pct)

    def test_simulate_scenario_symbol_not_found_raises_key_error(self):
        rand_symbol = f"MISSING_{uuid.uuid4().hex[:4]}"
        portfolio_data = {"OTHER_SYMBOL": {"current_price": 100, "quantity": 10}}
        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            with self.assertRaises(KeyError):
                self.simulator.simulate_scenario(rand_symbol, 5.0)

    def test_run_stress_test(self):
        rand_symbol = f"STRESS_{uuid.uuid4().hex[:4].upper()}"
        price = 100.0
        quantity = 10.0
        shifts = [-10, 0, 10]

        portfolio_data = {
            rand_symbol: {"current_price": price, "quantity": quantity}
        }

        with patch.object(self.simulator, 'load_data', return_value=portfolio_data):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), 3)
            self.assertEqual(report[0]["shift_percentage"], -10)
            self.assertAlmostEqual(report[0]["resulting_valuation"], 90.0)
            self.assertEqual(report[1]["shift_percentage"], 0)
            self.assertAlmostEqual(report[1]["resulting_valuation"], 100.0)
            self.assertEqual(report[2]["shift_percentage"], 10)
            self.assertAlmostEqual(report[2]["resulting_valuation"], 110.0)

    def test_run_stress_test_with_missing_symbol_graceful_handling(self):
        rand_symbol = f"GHOST_{uuid.uuid4().hex[:4].upper()}"
        shifts = [-5, 5]

        with patch.object(self.simulator, 'load_data', return_value={}):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), 2)
            self.assertEqual(report[0]["resulting_valuation"], 0.0)
            self.assertEqual(report[1]["resulting_valuation"], 0.0)

    def test_simulate_market_scenario_wrapper(self):
        rand_symbol = f"WRAP_{uuid.uuid4().hex[:4].upper()}"
        price = 200.0
        quantity = 5.0
        percentage = 20.0

        portfolio_data = {
            rand_symbol: {"current_price": price, "quantity": quantity}
        }

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=portfolio_data):
            res = simulate_market_scenario(self.random_storage, rand_symbol, percentage)
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["simulated_price"], 240.0)

    def test_run_stress_test_wrapper(self):
        rand_symbol = f"WSTRESS_{uuid.uuid4().hex[:4].upper()}"
        price = 50.0
        quantity = 2.0
        
        portfolio_data = {
            rand_symbol: {"current_price": price, "quantity": quantity}
        }

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=portfolio_data):
            result = run_stress_test(self.random_storage, rand_symbol, 0, 10, 5)
            self.assertEqual(result["symbol"], rand_symbol)
            self.assertIsInstance(result["scenarios"], list)
            self.assertGreaterEqual(len(result["scenarios"]), 1)