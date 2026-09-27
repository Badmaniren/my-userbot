import io
import json
import os
import random
import string
import tempfile
import unittest
from unittest.mock import mock_open, patch

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    run_stress_test,
    simulate_market_scenario,
)


class TestPortfolioScenarioSimulator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _generate_random_symbol(self):
        prefix = "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        suffix = uuid_val = random.randint(100, 999)
        return f"{prefix}_{suffix}"

    def _create_temp_portfolio_file(self, content):
        file_path = os.path.join(self.temp_dir.name, f"{random.randint(10000, 99999)}_portfolio.json")
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(content, (dict, list)):
                json.dump(content, f)
            else:
                f.write(str(content))
        return file_path

    def test_init_stores_storage_file(self):
        dummy_file = f"/tmp/{random.randint(1000, 9999)}_{self._generate_random_symbol()}.json"
        simulator = PortfolioScenarioSimulator(dummy_file)
        self.assertEqual(simulator.storage_file, dummy_file)

    def test_load_data_valid_json(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(10.0, 500.0), 2)
        payload = {symbol: {"price": price, "quantity": random.randint(1, 100)}}
        file_path = self._create_temp_portfolio_file(payload)

        simulator = PortfolioScenarioSimulator(file_path)
        data = simulator.load_data(file_path)
        self.assertIsInstance(data, dict)
        self.assertIn(symbol, data)
        self.assertEqual(data[symbol]["price"], price)

    def test_load_data_file_not_found(self):
        non_existent_file = os.path.join(self.temp_dir.name, f"absent_{random.randint(1000, 9999)}.json")
        simulator = PortfolioScenarioSimulator(non_existent_file)
        data = simulator.load_data(non_existent_file)
        self.assertEqual(data, {})

    def test_load_data_corrupted_json(self):
        corrupt_content = "{" + "".join(random.choices(string.ascii_letters, k=20))
        file_path = self._create_temp_portfolio_file(corrupt_content)
        simulator = PortfolioScenarioSimulator(file_path)
        data = simulator.load_data(file_path)
        self.assertEqual(data, {})

    def test_simulate_scenario_direct_key(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(50.0, 200.0), 4)
        quantity = round(random.uniform(5.0, 50.0), 4)
        shift_pct = round(random.uniform(-15.0, 25.0), 2)

        portfolio_data = {
            symbol: {
                "current_price": price,
                "quantity": quantity
            }
        }
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, shift_pct)

        expected_simulated_price = price * (1 + shift_pct / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)
        self.assertAlmostEqual(res["portfolio_value_delta"], expected_pnl, places=6)

    def test_simulate_scenario_assets_list_structure(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(10.0, 100.0), 4)
        quantity = round(random.uniform(1.0, 20.0), 4)
        shift_pct = round(random.uniform(1.0, 10.0), 2)

        portfolio_data = {
            "assets": [
                {"symbol": self._generate_random_symbol(), "price": 10.0, "shares": 1.0},
                {"symbol": symbol, "price": price, "shares": quantity}
            ]
        }
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, str(shift_pct))

        expected_simulated_price = price * (1 + shift_pct / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)

    def test_simulate_scenario_holdings_list_structure(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(20.0, 300.0), 4)
        quantity = round(random.uniform(10.0, 100.0), 4)
        shift_pct = round(random.uniform(-30.0, -5.0), 2)

        portfolio_data = {
            "holdings": [
                {"symbol": symbol, "current_price": price, "quantity": quantity},
                {"symbol": self._generate_random_symbol(), "current_price": 50.0, "quantity": 2.0}
            ]
        }
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, shift_pct)

        expected_simulated_price = price * (1 + shift_pct / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)

    def test_simulate_scenario_flat_dict_root(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(100.0, 500.0), 4)
        quantity = round(random.uniform(2.0, 15.0), 4)
        shift_pct = round(random.uniform(5.0, 20.0), 2)

        portfolio_data = {
            "symbol": symbol,
            "current_price": price,
            "quantity": quantity
        }
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, shift_pct)

        expected_simulated_price = price * (1 + shift_pct / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)

    def test_simulate_scenario_list_root(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(15.0, 85.0), 4)
        quantity = round(random.uniform(50.0, 150.0), 4)
        shift_pct = round(random.uniform(-10.0, 10.0), 2)

        portfolio_data = [
            {"symbol": self._generate_random_symbol(), "price": 42.0, "quantity": 10.0},
            {"symbol": symbol, "price": price, "quantity": quantity}
        ]
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, shift_pct)

        expected_simulated_price = price * (1 + shift_pct / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)

    def test_simulate_scenario_with_slippage_factor(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(100.0, 250.0), 4)
        quantity = round(random.uniform(10.0, 40.0), 4)
        shift_pct = round(random.uniform(5.0, 15.0), 2)
        slippage = round(random.uniform(0.5, 2.5), 2)

        portfolio_data = {
            symbol: {"current_price": price, "quantity": quantity}
        }
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, shift_pct, slippage_factor=slippage)

        base_simulated = price * (1.0 + shift_pct / 100.0)
        slippage_adj = base_simulated * (slippage / 100.0)
        expected_price = base_simulated + slippage_adj
        expected_pnl = (expected_price - price) * quantity

        self.assertAlmostEqual(res["simulated_price"], expected_price, places=6)
        self.assertAlmostEqual(res["pnl_impact"], expected_pnl, places=6)

    def test_simulate_scenario_missing_fields_default_to_zero(self):
        symbol = self._generate_random_symbol()
        portfolio_data = {symbol: {}}
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        res = simulator.simulate_scenario(symbol, 10.0)
        self.assertEqual(res["symbol"], symbol)
        self.assertEqual(res["simulated_price"], 0.0)
        self.assertEqual(res["pnl_impact"], 0.0)
        self.assertEqual(res["portfolio_value_delta"], 0.0)

    def test_simulate_scenario_symbol_not_found_raises_key_error(self):
        symbol = self._generate_random_symbol()
        absent_symbol = f"ABSENT_{random.randint(1000, 9999)}"
        portfolio_data = {symbol: {"price": 100.0, "quantity": 10.0}}
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        with self.assertRaises(KeyError):
            simulator.simulate_scenario(absent_symbol, 5.0)

    def test_simulate_scenario_invalid_symbol_inputs(self):
        file_path = self._create_temp_portfolio_file({})
        simulator = PortfolioScenarioSimulator(file_path)

        invalid_symbols = ["", "   ", None, 12345, [], {}]
        for invalid_sym in invalid_symbols:
            with self.assertRaises(ValueError):
                simulator.simulate_scenario(invalid_sym, 10.0)

    def test_simulate_scenario_invalid_percentage_inputs(self):
        symbol = self._generate_random_symbol()
        file_path = self._create_temp_portfolio_file({symbol: {"price": 10.0, "quantity": 1.0}})
        simulator = PortfolioScenarioSimulator(file_path)

        invalid_percentages = ["invalid_pct", "abc", None, [10], {}]
        for invalid_pct in invalid_percentages:
            with self.assertRaises(ValueError):
                simulator.simulate_scenario(symbol, invalid_pct)

    def test_run_stress_test_valid_shifts(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(50.0, 150.0), 4)
        quantity = round(random.uniform(5.0, 25.0), 4)
        portfolio_data = {symbol: {"price": price, "quantity": quantity}}
        file_path = self._create_temp_portfolio_file(portfolio_data)
        simulator = PortfolioScenarioSimulator(file_path)

        shifts = [round(random.uniform(-20.0, 20.0), 1) for _ in range(3)]
        report = simulator.run_stress_test(symbol, shifts)

        self.assertEqual(len(report), len(shifts))
        for idx, shift in enumerate(shifts):
            expected_price = round(price * (1 + shift / 100.0), 10)
            self.assertEqual(report[idx]["shift_percentage"], shift)
            self.assertAlmostEqual(report[idx]["resulting_valuation"], expected_price, places=6)

    def test_run_stress_test_handles_errors_gracefully(self):
        absent_symbol = f"NON_EXISTENT_{random.randint(1000, 9999)}"
        file_path = self._create_temp_portfolio_file({})
        simulator = PortfolioScenarioSimulator(file_path)

        shifts = [random.randint(-10, 10), "corrupt_shift"]
        report = simulator.run_stress_test(absent_symbol, shifts)

        self.assertEqual(len(report), 2)
        self.assertEqual(report[0]["resulting_valuation"], 0.0)
        self.assertEqual(report[0]["shift_percentage"], float(shifts[0]))
        self.assertEqual(report[1]["resulting_valuation"], 0.0)
        self.assertEqual(report[1]["shift_percentage"], 0.0)

    def test_simulate_market_scenario_wrapper(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(30.0, 90.0), 4)
        quantity = round(random.uniform(1.0, 10.0), 4)
        shift = round(random.uniform(-5.0, 15.0), 2)

        portfolio_data = {symbol: {"price": price, "quantity": quantity}}
        file_path = self._create_temp_portfolio_file(portfolio_data)

        result = simulate_market_scenario(file_path, symbol, shift)

        expected_simulated_price = price * (1 + shift / 100.0)
        expected_pnl = (expected_simulated_price - price) * quantity

        self.assertEqual(result["symbol"], symbol)
        self.assertAlmostEqual(result["simulated_price"], expected_simulated_price, places=6)
        self.assertAlmostEqual(result["pnl_impact"], expected_pnl, places=6)

    def test_run_stress_test_wrapper(self):
        symbol = self._generate_random_symbol()
        price = round(random.uniform(40.0, 120.0), 4)
        quantity = round(random.uniform(2.0, 8.0), 4)
        portfolio_data = {symbol: {"price": price, "quantity": quantity}}
        file_path = self._create_temp_portfolio_file(portfolio_data)

        range_min = -10
        range_max = 10
        step = 10
        expected_shifts = [-10.0, 0.0, 10.0]

        res = run_stress_test(file_path, symbol, range_min, range_max, step)

        self.assertEqual(res["symbol"], symbol)
        self.assertIn("scenarios", res)
        scenarios = res["scenarios"]
        self.assertEqual(len(scenarios), len(expected_shifts))

        for idx, shift in enumerate(expected_shifts):
            self.assertEqual(scenarios[idx]["shift_percentage"], shift)
            expected_price = round(price * (1 + shift / 100.0), 10)
            self.assertAlmostEqual(scenarios[idx]["resulting_valuation"], expected_price, places=6)


if __name__ == "__main__":
    unittest.main()