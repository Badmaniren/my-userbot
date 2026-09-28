import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import string
import io

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)

class TestPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.simulator = PortfolioScenarioSimulator(self.rand_storage)

    def test_load_data_success(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_price = round(random.uniform(10.0, 1000.0), 4)
        rand_qty = round(random.uniform(1.0, 100.0), 4)
        
        mock_data = {
            "assets": [
                {
                    "symbol": rand_symbol,
                    "current_price": rand_price,
                    "quantity": rand_qty
                }
            ]
        }
        mock_json_str = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=mock_json_str)):
            data = self.simulator.load_data(self.simulator.storage_file)
            self.assertEqual(data, mock_data)

    def test_load_data_io_error(self):
        with patch("builtins.open", side_effect=IOError("Disk explosion")):
            data = self.simulator.load_data(self.simulator.storage_file)
            self.assertEqual(data, {})

    def test_load_data_json_decode_error(self):
        corrupted_bytes = io.StringIO("INVALID_JSON_" + uuid.uuid4().hex)
        with patch("builtins.open", return_value=corrupted_bytes):
            data = self.simulator.load_data(self.simulator.storage_file)
            self.assertEqual(data, {})

    def test_simulate_scenario_validation_errors(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        with self.assertRaises(ValueError):
            self.simulator.simulate_scenario("", 10.0)

        with self.assertRaises(ValueError):
            self.simulator.simulate_scenario("   ", 10.0)

        with self.assertRaises(ValueError):
            self.simulator.simulate_scenario(12345, 10.0)

        with self.assertRaises(ValueError):
            self.simulator.simulate_scenario(rand_symbol, "NOT_A_FLOAT")

    def test_simulate_scenario_key_error(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        missing_portfolio = {"assets": []}
        
        with patch.object(self.simulator, "load_data", return_value=missing_portfolio):
            with self.assertRaises(KeyError):
                self.simulator.simulate_scenario(rand_symbol, 5.0)

    def test_simulate_scenario_success_dict_assets(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_price = round(random.uniform(50.0, 500.0), 2)
        rand_qty = round(random.uniform(2.0, 50.0), 2)
        rand_pct = round(random.uniform(-20.0, 20.0), 2)
        rand_slippage = round(random.uniform(0.0, 2.0), 2)

        portfolio_data = {
            "assets": [
                {
                    "symbol": rand_symbol,
                    "price": rand_price,
                    "shares": rand_qty
                }
            ]
        }

        with patch.object(self.simulator, "load_data", return_value=portfolio_data):
            res = self.simulator.simulate_scenario(rand_symbol, rand_pct, rand_slippage)
            
            self.assertEqual(res["symbol"], rand_symbol)
            base_price = rand_price * (1 + rand_pct / 100.0)
            slip_adj = base_price * (rand_slippage / 100.0)
            expected_price = base_price + slip_adj
            expected_pnl = (expected_price - rand_price) * rand_qty

            self.assertAlmostEqual(res["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=4)
            self.assertAlmostEqual(res["portfolio_value_delta"], expected_pnl, places=4)

    def test_simulate_scenario_success_holdings_list(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_price = round(random.uniform(10.0, 100.0), 2)
        rand_qty = round(random.uniform(10.0, 200.0), 2)
        rand_pct = round(random.uniform(1.0, 10.0), 2)

        portfolio_data = {
            "holdings": [
                {
                    "symbol": rand_symbol,
                    "current_price": rand_price,
                    "quantity": rand_qty
                }
            ]
        }

        with patch.object(self.simulator, "load_data", return_value=portfolio_data):
            res = self.simulator.simulate_scenario(rand_symbol, rand_pct)
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertIn("simulated_price", res)
            self.assertIn("pnl_impact", res)

    def test_run_stress_test(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]
        
        mock_result = {
            "symbol": rand_symbol,
            "simulated_price": 150.5,
            "pnl_impact": 500.0,
            "portfolio_value_delta": 500.0
        }

        with patch.object(self.simulator, "simulate_scenario", return_value=mock_result):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), len(shifts))
            for i, step in enumerate(shifts):
                self.assertEqual(report[i]["shift_percentage"], float(step))
                self.assertEqual(report[i]["resulting_valuation"], 150.5)

    def test_run_stress_test_with_exceptions(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        shifts = [10, 20]

        with patch.object(self.simulator, "simulate_scenario", side_effect=KeyError("Missing")):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), 2)
            self.assertEqual(report[0]["resulting_valuation"], 0.0)
            self.assertEqual(report[1]["resulting_valuation"], 0.0)

    def test_simulate_market_scenario_wrapper(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_pct = round(random.uniform(-5.0, 5.0), 2)
        rand_storage = f"{uuid.uuid4().hex}.json"

        mock_return = {"symbol": rand_symbol, "simulated_price": 99.9, "pnl_impact": 1.0, "portfolio_value_delta": 1.0}

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario", return_value=mock_return) as mock_sim:
            res = simulate_market_scenario(rand_storage, rand_symbol, rand_pct)
            mock_sim.assert_called_once_with(rand_symbol, rand_pct)
            self.assertEqual(res, mock_return)

    def test_run_stress_test_wrapper(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_storage = f"{uuid.uuid4().hex}.json"
        
        mock_report = [{"shift_percentage": 0.0, "resulting_valuation": 100.0}]

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test", return_value=mock_report) as mock_stress:
            res = run_stress_test(rand_storage, rand_symbol, 0, 10, 10)
            mock_stress.assert_called_once_with(rand_symbol, [0.0, 10.0])
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertEqual(res["scenarios"], mock_report)