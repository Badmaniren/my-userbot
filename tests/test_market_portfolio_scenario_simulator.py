import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json

from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario, run_stress_test

class TestPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.simulator = PortfolioScenarioSimulator(self.storage_file)

    def test_load_data_success(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        rand_qty = round(random.uniform(1.0, 50.0), 4)
        mock_data = {
            "symbol": rand_symbol,
            "current_price": rand_price,
            "quantity": rand_qty
        }
        json_content = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=json_content)):
            data = self.simulator.load_data(self.storage_file)
            self.assertEqual(data.get("symbol"), rand_symbol)
            self.assertEqual(data.get("current_price"), rand_price)
            self.assertEqual(data.get("quantity"), rand_qty)

    def test_load_data_failure(self):
        with patch("builtins.open", side_effect=IOError("Random I/O Error")):
            data = self.simulator.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_simulate_scenario_dict_format(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(50.0, 500.0), 2)
        rand_qty = round(random.uniform(2.0, 20.0), 2)
        percentage = round(random.uniform(-20.0, 20.0), 2)

        mock_portfolio = {
            "symbol": rand_symbol,
            "price": rand_price,
            "shares": rand_qty
        }

        with patch.object(self.simulator, "load_data", return_value=mock_portfolio):
            res = self.simulator.simulate_scenario(rand_symbol, percentage)
            expected_price = rand_price * (1 + percentage / 100.0)
            expected_pnl = (expected_price - rand_price) * rand_qty

            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=4)
            self.assertAlmostEqual(res["portfolio_value_delta"], expected_pnl, places=4)

    def test_simulate_scenario_assets_list_format(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = round(random.uniform(10.0, 200.0), 2)
        rand_qty = round(random.uniform(1.0, 10.0), 2)
        percentage = round(random.uniform(5.0, 15.0), 2)

        mock_portfolio = {
            "assets": [
                {
                    "symbol": uuid.uuid4().hex[:6].upper(),
                    "current_price": 10.0,
                    "quantity": 1.0
                },
                {
                    "symbol": rand_symbol,
                    "current_price": rand_price,
                    "quantity": rand_qty
                }
            ]
        }

        with patch.object(self.simulator, "load_data", return_value=mock_portfolio):
            res = self.simulator.simulate_scenario(rand_symbol, percentage)
            expected_price = rand_price * (1 + percentage / 100.0)
            expected_pnl = (expected_price - rand_price) * rand_qty

            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["simulated_price"], expected_price, places=4)
            self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=4)

    def test_simulate_scenario_invalid_symbol_raises_value_error(self):
        invalid_symbols = ["", "   ", 12345, None]
        for sym in invalid_symbols:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(sym, 10.0)

    def Test_simulate_scenario_invalid_percentage_raises_value_error(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        invalid_percentages = ["abc", {}, []]
        for pct in invalid_percentages:
            with self.assertRaises(ValueError):
                self.simulator.simulate_scenario(rand_symbol, pct)

    def test_simulate_scenario_symbol_not_found_raises_key_error(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        missing_symbol = uuid.uuid4().hex[:6].upper()
        mock_portfolio = {
            "symbol": rand_symbol,
            "current_price": 100.0,
            "quantity": 5.0
        }

        with patch.object(self.simulator, "load_data", return_value=mock_portfolio):
            with self.assertRaises(KeyError):
                self.simulator.simulate_scenario(missing_symbol, 5.0)

    def test_run_stress_test(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = 100.0
        rand_qty = 10.0
        shifts = [-10, 0, 10]

        mock_portfolio = {
            "symbol": rand_symbol,
            "current_price": rand_price,
            "quantity": rand_qty
        }

        with patch.object(self.simulator, "load_data", return_value=mock_portfolio):
            report = self.simulator.run_stress_test(rand_symbol, shifts)
            self.assertEqual(len(report), 3)
            self.assertEqual(report[0]["shift_percentage"], -10.0)
            self.assertEqual(report[0]["resulting_valuation"], 90.0)
            self.assertEqual(report[1]["shift_percentage"], 0.0)
            self.assertEqual(report[1]["resulting_valuation"], 100.0)
            self.assertEqual(report[2]["shift_percentage"], 10.0)
            self.assertEqual(report[2]["resulting_valuation"], 110.0)

    def test_wrapper_simulate_market_scenario(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = 50.0
        rand_qty = 2.0
        percentage = 10.0
        mock_portfolio = {
            "symbol": rand_symbol,
            "current_price": rand_price,
            "quantity": rand_qty
        }

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=mock_portfolio):
            res = simulate_market_scenario(self.storage_file, rand_symbol, percentage)
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["simulated_price"], 55.0)

    def test_wrapper_run_stress_test(self):
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_price = 200.0
        rand_qty = 5.0
        mock_portfolio = {
            "symbol": rand_symbol,
            "current_price": rand_price,
            "quantity": rand_qty
        }

        with patch("skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data", return_value=mock_portfolio):
            result = run_stress_test(self.storage_file, rand_symbol, 0, 10, 5)
            self.assertEqual(result["symbol"], rand_symbol)
            self.assertEqual(len(result["scenarios"]), 3)
            self.assertEqual(result["scenarios"][0]["shift_percentage"], 0.0)
            self.assertEqual(result["scenarios"][0]["resulting_valuation"], 200.0)
            self.assertEqual(result["scenarios"][1]["shift_percentage"], 5.0)
            self.assertEqual(result["scenarios"][1]["resulting_valuation"], 210.0)
            self.assertEqual(result["scenarios"][2]["shift_percentage"], 10.0)
            self.assertEqual(result["scenarios"][2]["resulting_valuation"], 220.0)

if __name__ == "__main__":
    unittest.main()