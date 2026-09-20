import unittest
from unittest.mock import patch
import json
import os
import uuid
import random
from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)

class TestMarketPortfolioScenarioSimulator(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.current_price = round(random.uniform(10.0, 500.0), 2)
        self.quantity = round(random.uniform(1.0, 50.0), 2)
        
        self.test_data = {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "quantity": self.quantity
        }
        with open(self.storage_file, 'w') as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_load_data_success(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        data = simulator.load_data(self.storage_file)
        self.assertEqual(data.get("symbol"), self.symbol)

    def test_load_data_failure(self):
        bad_file = f"bad_{uuid.uuid4().hex}.json"
        simulator = PortfolioScenarioSimulator(bad_file)
        data = simulator.load_data(bad_file)
        self.assertEqual(data, {})

    def test_simulate_scenario_dict_root(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        percentage = 10.0
        res = simulator.simulate_scenario(self.symbol, percentage)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        expected_impact = (expected_price - self.current_price) * self.quantity
        
        self.assertEqual(res["symbol"], self.symbol)
        self.assertAlmostEqual(res["simulated_price"], expected_price)
        self.assertAlmostEqual(res["pnl_impact"], expected_impact)
        self.assertAlmostEqual(res["portfolio_value_delta"], expected_impact)

    def test_simulate_scenario_assets_list(self):
        assets_data = {
            "assets": [
                {
                    "symbol": self.symbol,
                    "price": self.current_price,
                    "shares": self.quantity
                }
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(assets_data, f)
            
        simulator = PortfolioScenarioSimulator(self.storage_file)
        percentage = -15.5
        res = simulator.simulate_scenario(self.symbol, percentage)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        expected_impact = (expected_price - self.current_price) * self.quantity
        
        self.assertAlmostEqual(res["simulated_price"], expected_price)
        self.assertAlmostEqual(res["pnl_impact"], expected_impact)

    def test_simulate_scenario_holdings_list(self):
        holdings_data = {
            "holdings": [
                {
                    "symbol": self.symbol,
                    "current_price": self.current_price,
                    "quantity": self.quantity
                }
            ]
        }
        with open(self.storage_file, 'w') as f:
            json.dump(holdings_data, f)
            
        simulator = PortfolioScenarioSimulator(self.storage_file)
        percentage = 20.0
        res = simulator.simulate_scenario(self.symbol, percentage)
        
        expected_price = self.current_price * (1 + percentage / 100.0)
        self.assertAlmostEqual(res["simulated_price"], expected_price)

    def test_simulate_scenario_list_root(self):
        list_data = [
            {
                "symbol": self.symbol,
                "current_price": self.current_price,
                "quantity": self.quantity
            }
        ]
        with open(self.storage_file, 'w') as f:
            json.dump(list_data, f)
            
        simulator = PortfolioScenarioSimulator(self.storage_file)
        percentage = 5.0
        res = simulator.simulate_scenario(self.symbol, percentage)
        self.assertEqual(res["symbol"], self.symbol)

    def test_simulate_scenario_not_found(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        missing_symbol = f"MISS_{uuid.uuid4().hex[:6]}"
        with self.assertRaises(KeyError):
            simulator.simulate_scenario(missing_symbol, 10.0)

    def test_run_stress_test(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        shifts = [-10.0, 0.0, 10.0]
        report = simulator.run_stress_test(self.symbol, shifts)
        
        self.assertEqual(len(report), 3)
        for i, shift in enumerate(shifts):
            self.assertEqual(report[i]["shift_percentage"], shift)
            expected_val = self.current_price * (1 + shift / 100.0)
            self.assertAlmostEqual(report[i]["resulting_valuation"], expected_val)

    def test_run_stress_test_with_exception(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        missing_symbol = f"MISS_{uuid.uuid4().hex[:6]}"
        shifts = [5.0, 10.0]
        report = simulator.run_stress_test(missing_symbol, shifts)
        
        self.assertEqual(len(report), 2)
        for item in report:
            self.assertEqual(item["resulting_valuation"], 0.0)

    def test_simulate_market_scenario_helper(self):
        percentage = 12.5
        res = simulate_market_scenario(self.storage_file, self.symbol, percentage)
        expected_price = self.current_price * (1 + percentage / 100.0)
        self.assertAlmostEqual(res["simulated_price"], expected_price)

    def test_run_stress_test_helper(self):
        range_min = -5.0
        range_max = 5.0
        step = 5
        result = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
        
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIsInstance(result["scenarios"], list)
        self.assertGreaterEqual(len(result["scenarios"]), 1)