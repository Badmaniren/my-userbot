import unittest
from unittest.mock import patch, MagicMock
import json
import os
import random
import uuid
import io

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)

class TestMarketPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_storage = f"portfolio_{uuid.uuid4().hex[:8]}.json"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.random_quantity = round(random.uniform(1.0, 100.0), 4)
        self.random_percentage = round(random.uniform(-50.0, 50.0), 2)

    def test_simulate_scenario_success_dict_format(self):
        mock_data = {
            "symbol": self.random_symbol,
            "current_price": self.random_price,
            "quantity": self.random_quantity
        }

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            
            simulator = PortfolioScenarioSimulator(self.random_storage)
            result = simulator.simulate_scenario(self.random_symbol, self.random_percentage)

            self.assertEqual(result["symbol"], self.random_symbol)
            expected_price = self.random_price * (1 + self.random_percentage / 100.0)
            self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)
            expected_pnl = (expected_price - self.random_price) * self.random_quantity
            self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=4)

    def test_simulate_scenario_success_list_format(self):
        mock_data = [
            {
                "symbol": self.random_symbol,
                "price": self.random_price,
                "shares": self.random_quantity
            }
        ]

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):

            simulator = PortfolioScenarioSimulator(self.random_storage)
            result = simulator.simulate_scenario(self.random_symbol, self.random_percentage)

            self.assertEqual(result["symbol"], self.random_symbol)
            expected_price = self.random_price * (1 + self.random_percentage / 100.0)
            self.assertAlmostEqual(result["simulated_price"], expected_price, places=4)

    def test_simulate_scenario_invalid_symbol(self):
        simulator = PortfolioScenarioSimulator(self.random_storage)
        invalid_symbols = ["", "   ", None, 12345]

        for inv_sym in invalid_symbols:
            with self.subTest(inv_sym=inv_sym):
                with self.assertRaises(ValueError):
                    simulator.simulate_scenario(inv_sym, self.random_percentage)

    def test_simulate_scenario_invalid_percentage(self):
        simulator = PortfolioScenarioSimulator(self.random_storage)
        invalid_percentages = ["not_a_number", None, {}]

        for inv_pct in invalid_percentages:
            with self.subTest(inv_pct=inv_pct):
                with self.assertRaises(ValueError):
                    simulator.simulate_scenario(self.random_symbol, inv_pct)

    def test_simulate_scenario_symbol_not_found(self):
        mock_data = {"symbol": f"OTHER_{uuid.uuid4().hex[:4]}", "current_price": 10.0, "quantity": 1.0}

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):

            simulator = PortfolioScenarioSimulator(self.random_storage)
            with self.assertRaises(KeyError):
                simulator.simulate_scenario(self.random_symbol, self.random_percentage)

    def test_run_stress_test(self):
        mock_data = {
            "symbol": self.random_symbol,
            "current_price": self.random_price,
            "quantity": self.random_quantity
        }
        shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):

            simulator = PortfolioScenarioSimulator(self.random_storage)
            report = simulator.run_stress_test(self.random_symbol, shifts)

            self.assertEqual(len(report), len(shifts))
            for i, step_res in enumerate(report):
                self.assertEqual(step_res["shift_percentage"], float(shifts[i]))
                expected_valuation = self.random_price * (1 + shifts[i] / 100.0)
                self.assertAlmostEqual(step_res["resulting_valuation"], expected_valuation, places=4)

    def test_simulate_market_scenario_wrapper(self):
        mock_data = {
            "symbol": self.random_symbol,
            "current_price": self.random_price,
            "quantity": self.random_quantity
        }

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):

            result = simulate_market_scenario(self.random_storage, self.random_symbol, self.random_percentage)
            self.assertEqual(result["symbol"], self.random_symbol)

    def test_run_stress_test_wrapper(self):
        mock_data = {
            "symbol": self.random_symbol,
            "current_price": self.random_price,
            "quantity": self.random_quantity
        }
        rmin = random.randint(-5, -2)
        rmax = random.randint(2, 5)
        step = random.randint(1, 2)

        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", return_value=None), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_data))):

            result = run_stress_test(self.random_storage, self.random_symbol, rmin, rmax, step)
            self.assertEqual(result["symbol"], self.random_symbol)
            self.assertIn("scenarios", result)
            self.assertGreater(len(result["scenarios"]), 0)

    def test_load_data_io_exception(self):
        with patch("skills.market_portfolio_scenario_simulator.os.path.exists", return_value=True), \
             patch("skills.market_portfolio_scenario_simulator.load_portfolio", side_effect=Exception("DB Failure")), \
             patch("builtins.open", side_effect=IOError("Disk error")):

            simulator = PortfolioScenarioSimulator(self.random_storage)
            data = simulator.load_data(self.random_storage)
            self.assertEqual(data, {})

if __name__ == '__main__':
    unittest.main()