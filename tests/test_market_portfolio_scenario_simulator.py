import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json

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

    def test_init_sets_storage_file(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        self.assertEqual(simulator.storage_file, self.storage_file)
        self.assertIsNotNone(simulator.parser)
        self.assertIsNotNone(simulator.valuation)
        self.assertIsNotNone(simulator.slippage_model)

    def test_load_data_success(self):
        random_data = {
            self.symbol: {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            data = simulator.load_data(self.storage_file)
            self.assertEqual(data, random_data)

    def test_simulate_scenario_invalid_symbol_raises_value_error(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        for bad_symbol in ["", "   ", None, 123]:
            with self.subTest(bad_symbol=bad_symbol):
                with self.assertRaises(ValueError):
                    simulator.simulate_scenario(bad_symbol, self.percentage)

    def test_simulate_scenario_invalid_percentage_raises_value_error(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        for bad_pct in ["not-a-number", None, {}]:
            with self.subTest(bad_pct=bad_pct):
                with self.assertRaises(ValueError):
                    simulator.simulate_scenario(self.symbol, bad_pct)

    def test_simulate_scenario_symbol_not_found_raises_key_error(self):
        random_data = {
            f"OTHER_{uuid.uuid4().hex[:4]}": {
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        }
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            with self.assertRaises(KeyError):
                simulator.simulate_scenario(self.symbol, self.percentage)

    def test_simulate_scenario_dict_structures_success(self):
        structures = [
            {self.symbol: {"current_price": self.current_price, "quantity": self.quantity}},
            {"assets": [{"symbol": self.symbol, "price": self.current_price, "shares": self.quantity}]},
            {"holdings": [{"symbol": self.symbol, "current_price": self.current_price, "quantity": self.quantity}]},
            {"symbol": self.symbol, "current_price": self.current_price, "quantity": self.quantity}
        ]

        for struct in structures:
            with self.subTest(struct=struct):
                mock_file_content = json.dumps(struct)
                with patch("builtins.open", mock_open(read_data=mock_file_content)):
                    simulator = PortfolioScenarioSimulator(self.storage_file)
                    with patch.object(simulator.slippage_model, "apply_slippage", return_value=self.current_price * (1 + self.percentage / 100.0)) as mock_slippage:
                        res = simulator.simulate_scenario(self.symbol, self.percentage)
                        self.assertEqual(res["symbol"], self.symbol)
                        self.assertIn("simulated_price", res)
                        self.assertIn("pnl_impact", res)
                        self.assertIn("portfolio_value_delta", res)
                        mock_slippage.assert_called_once()

    def test_simulate_scenario_list_structure_success(self):
        struct = [{"symbol": self.symbol, "current_price": self.current_price, "quantity": self.quantity}]
        mock_file_content = json.dumps(struct)
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            with patch.object(simulator.slippage_model, "apply_slippage", side_effect=Exception("Slippage error")):
                res = simulator.simulate_scenario(self.symbol, self.percentage)
                self.assertEqual(res["symbol"], self.symbol)
                expected_sim_price = self.current_price * (1 + self.percentage / 100.0)
                self.assertAlmostEqual(res["simulated_price"], expected_sim_price)

    def test_run_stress_test(self):
        random_shifts = [random.randint(-10, -1), 0, random.randint(1, 10)]
        random_data = {self.symbol: {"current_price": self.current_price, "quantity": self.quantity}}
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            report = simulator.run_stress_test(self.symbol, random_shifts)
            self.assertEqual(len(report), len(random_shifts))
            for item in report:
                self.assertIn("shift_percentage", item)
                self.assertIn("resulting_valuation", item)

    def test_run_stress_test_handles_exceptions(self):
        random_shifts = ["invalid_shift", self.symbol]
        random_data = {self.symbol: {"current_price": self.current_price, "quantity": self.quantity}}
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            report = simulator.run_stress_test(self.symbol, random_shifts)
            self.assertEqual(len(report), 2)
            for item in report:
                self.assertEqual(item["resulting_valuation"], 0.0)

    def test_wrapper_simulate_market_scenario(self):
        random_data = {self.symbol: {"current_price": self.current_price, "quantity": self.quantity}}
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            res = simulate_market_scenario(self.storage_file, self.symbol, self.percentage)
            self.assertEqual(res["symbol"], self.symbol)

    def test_wrapper_run_stress_test(self):
        rmin = random.randint(-5, -2)
        rmax = random.randint(2, 5)
        step = random.randint(1, 2)
        random_data = {self.symbol: {"current_price": self.current_price, "quantity": self.quantity}}
        mock_file_content = json.dumps(random_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            res = run_stress_test(self.storage_file, self.symbol, rmin, rmax, step)
            self.assertEqual(res["symbol"], self.symbol)
            self.assertIn("scenarios", res)
            self.assertIsInstance(res["scenarios"], list)


if __name__ == "__main__":
    unittest.main()