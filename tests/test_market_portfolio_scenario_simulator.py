import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import os

from skills.market_portfolio_scenario_simulator import (
    PortfolioScenarioSimulator,
    simulate_market_scenario,
    run_stress_test
)

class TestMarketPortfolioScenarioSimulator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        
        self.initial_data = {
            "symbol": self.symbol,
            "quantity": round(random.uniform(10.0, 1000.0), 2),
            "purchase_price": round(random.uniform(50.0, 500.0), 2),
            "current_price": round(random.uniform(60.0, 600.0), 2)
        }

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_simulator_initialization(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        self.assertEqual(simulator.storage_file, self.storage_file)

    def test_load_data_success(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.initial_data, f)

        simulator = PortfolioScenarioSimulator(self.storage_file)
        loaded = simulator.load_data(self.storage_file)
        
        self.assertEqual(loaded.get("symbol"), self.initial_data["symbol"])
        self.assertEqual(loaded.get("quantity"), self.initial_data["quantity"])

    def test_load_data_invalid_io(self):
        bad_path = f"nonexistent_{uuid.uuid4().hex}.json"
        simulator = PortfolioScenarioSimulator(bad_path)
        with patch('builtins.open', side_effect=IOError("Disk explosion")):
            data = simulator.load_data(bad_path)
            self.assertIsInstance(data, (dict, list))

    def test_simulate_price_drop_scenario(self):
        percentage = round(random.uniform(5.0, 50.0), 2)
        mock_data = {
            self.symbol: self.initial_data
        }
        
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data', return_value=mock_data):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, -percentage)
            
            expected_simulated_price = self.initial_data["current_price"] * (1 - percentage / 100.0)
            self.assertIn("simulated_price", result)
            self.assertAlmostEqual(result["simulated_price"], expected_simulated_price, places=2)
            self.assertIn("pnl_impact", result)

    def test_simulate_price_surge_scenario(self):
        percentage = round(random.uniform(1.0, 99.0), 2)
        mock_data = {
            "assets": [self.initial_data]
        }
        
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data', return_value=mock_data):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            result = simulator.simulate_scenario(self.symbol, percentage)
            
            self.assertIsNotNone(result)
            self.assertIn("portfolio_value_delta", result)

    def test_run_stress_test_multiparams(self):
        steps = random.randint(3, 10)
        shifts = [round(random.uniform(-50.0, 50.0), 2) for _ in range(steps)]
        
        mock_payload = {
            "holdings": [
                {
                    "symbol": self.symbol,
                    "shares": random.randint(1, 100),
                    "price": round(random.uniform(10.0, 1000.0), 2)
                }
            ]
        }

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data', return_value=mock_payload):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            report = simulator.run_stress_test(self.symbol, shifts)
            
            self.assertIsInstance(report, list)
            self.assertEqual(len(report), len(shifts))
            for item in report:
                self.assertIn("shift_percentage", item)
                self.assertIn("resulting_valuation", item)

    def test_standalone_simulate_market_scenario(self):
        target_shift = round(random.uniform(-30.0, 30.0), 2)
        random_stream = io.BytesIO(json.dumps(self.initial_data).encode('utf-8'))
        
        with patch('skills.market_portfolio_scenario_simulator.open', return_value=random_stream):
            res = simulate_market_scenario(self.storage_file, self.symbol, target_shift)
            self.assertIsInstance(res, dict)

    def test_standalone_run_stress_test(self):
        range_min = -20
        range_max = 20
        step = 5
        
        mock_return = {
            "symbol": self.symbol,
            "current_price": 100.0,
            "shares": 10
        }
        
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data', return_value=mock_return):
            stress_results = run_stress_test(self.storage_file, self.symbol, range_min, range_max, step)
            self.assertIsInstance(stress_results, dict)
            self.assertIn("scenarios", stress_results)

    def test_simulator_edge_case_missing_symbol(self):
        wrong_symbol = f"FAIL_{uuid.uuid4().hex[:4]}"
        mock_data = {
            "symbol": self.symbol,
            "price": 500.0
        }
        
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.load_data', return_value=mock_data):
            simulator = PortfolioScenarioSimulator(self.storage_file)
            with self.assertRaises((KeyError, ValueError, TypeError)):
                simulator.simulate_scenario(wrong_symbol, 15.0)

if __name__ == '__main__':
    unittest.main()