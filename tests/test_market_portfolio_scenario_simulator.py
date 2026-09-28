import unittest
from unittest.mock import patch, mock_open
import json
import os
import uuid
import random
import io
import tempfile

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
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(10.0, 1000.0), 4)
        mock_content = json.dumps({rand_symbol: {"current_price": rand_price, "quantity": 10.0}})
        
        with patch("builtins.open", mock_open(read_data=mock_content)):
            data = self.simulator.load_data(self.random_storage)
            self.assertIn(rand_symbol, data)
            self.assertEqual(data[rand_symbol]["current_price"], rand_price)

    def test_load_data_io_error(self):
        with patch("builtins.open", side_effect=IOError("Disk failure")):
            data = self.simulator.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_load_data_json_decode_error(self):
        with patch("builtins.open", mock_open(read_data="corrupted json")):
            data = self.simulator.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_simulate_scenario_invalid_symbol(self):
        invalid_symbols = ["", None, 123, "   "]
        for sym in invalid_symbols:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(sym, 10.0)

    def test_simulate_scenario_invalid_percentage(self):
        rand_symbol = uuid.uuid4().hex[:8]
        invalid_percentages = ["abc", None, {}]
        for pct in invalid_percentages:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(rand_symbol, pct)

    def test_simulate_scenario_symbol_not_found(self):
        rand_symbol = uuid.uuid4().hex[:8]
        other_symbol = uuid.uuid4().hex[:8]
        mock_data = json.dumps({other_symbol: {"current_price": 100.0, "quantity": 5.0}})
        
        with patch.object(self.simulator, 'load_data', return_value=json.loads(mock_data)):
            with self.assertRaises(KeyError):
                self.simulator.simulate_scenario(rand_symbol, 5.0)

    def test_simulate_scenario_dict_structures(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(50.0, 500.0), 2)
        rand_qty = round(random.uniform(1.0, 50.0), 2)
        rand_shift = round(random.uniform(-20.0, 20.0), 2)
        rand_slippage = round(random.uniform(0.1, 1.0), 2)

        structures = [
            {rand_symbol: {"current_price": rand_price, "quantity": rand_qty}},
            {"assets": [{"symbol": rand_symbol, "price": rand_price, "shares": rand_qty}]},
            {"holdings": [{"symbol": rand_symbol, "current_price": rand_price, "quantity": rand_qty}]},
            {"symbol": rand_symbol, "current_price": rand_price, "quantity": rand_qty},
            [{"symbol": rand_symbol, "current_price": rand_price, "quantity": rand_qty}]
        ]

        for struct in structures:
            with patch.object(self.simulator, 'load_data', return_value=struct):
                res = self.simulator.simulate_scenario(rand_symbol, rand_shift, rand_slippage)
                self.assertEqual(res["symbol"], rand_symbol)
                self.assertIsInstance(res["simulated_price"], float)
                self.assertIsInstance(res["pnl_impact"], float)
                self.assertIsInstance(res["portfolio_value_delta"], float)

    def test_run_stress_test_execution(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(100.0, 200.0), 2)
        mock_data = {rand_symbol: {"current_price": rand_price, "quantity": 10.0}}
        shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]

        with patch.object(self.simulator, 'load_data', return_value=mock_data):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), len(shifts))
            for item in report:
                self.assertIn("shift_percentage", item)
                self.assertIn("resulting_valuation", item)

    def test_run_stress_test_exception_handling(self):
        rand_symbol = uuid.uuid4().hex[:8]
        shifts = [10, 20]

        with patch.object(self.simulator, 'simulate_scenario', side_effect=KeyError("Missing")):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            for item in report:
                self.assertEqual(item["resulting_valuation"], 0.0)

    def test_wrapper_simulate_market_scenario(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(10.0, 50.0), 2)
        mock_data = json.dumps({rand_symbol: {"current_price": rand_price, "quantity": 5.0}})
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            res = simulate_market_scenario(self.random_storage, rand_symbol, 15.0)
            self.assertEqual(res["symbol"], rand_symbol)

    def test_wrapper_run_stress_test(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(50.0, 100.0), 2)
        mock_data = json.dumps({rand_symbol: {"current_price": rand_price, "quantity": 2.0}})
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            result = run_stress_test(self.random_storage, rand_symbol, -10, 10, 5)
            self.assertEqual(result["symbol"], rand_symbol)
            self.assertIn("scenarios", result)
            self.assertGreater(len(result["scenarios"]), 0)

if __name__ == "__main__":
    unittest.main()