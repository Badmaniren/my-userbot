import unittest
import os
import json
import uuid
from skills.market_portfolio_monte_carlo import PortfolioMonteCarloSimulator

class TestPortfolioMonteCarloIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, "portfolio_data.json")

        self.symbol = "SYM_" + uuid.uuid4().hex[:6].upper()
        self.initial_capital = float(round(10000 + uuid.uuid4().int % 5000, 2))
        self.simulations = 50
        self.days = 15

        historical_data = {
            self.symbol: [
                {"price": 100.0 + (i % 5), "return": 0.01 * (1 if i % 2 == 0 else -1)}
                for i in range(20)
            ]
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_run_simulation_integration(self):
        simulator = PortfolioMonteCarloSimulator(storage_filepath=self.storage_file)
        result = simulator.run_simulation(
            symbol=self.symbol,
            initial_capital=self.initial_capital,
            simulations=self.simulations,
            days=self.days
        )

        self.assertIn("mean_final_value", result)
        self.assertIn("percentile_5", result)
        self.assertIn("percentile_95", result)
        self.assertIn("simulation_matrix", result)
        self.assertIn("mean_return", result)
        self.assertIn("var", result)
        self.assertIn("cvar", result)
        self.assertEqual(result["symbol"], self.symbol)

        self.assertEqual(len(result["simulation_matrix"]), self.simulations)
        self.assertGreater(result["mean_final_value"], 0.0)

    def test_generate_monte_carlo_report_integration(self):
        simulator = PortfolioMonteCarloSimulator(storage_filepath=self.storage_file)
        report = simulator.generate_monte_carlo_report(
            symbol=self.symbol,
            days=self.days,
            simulations=self.simulations,
            initial_capital=self.initial_capital
        )

        self.assertIsInstance(report, dict)
        self.assertEqual(report["symbol"], self.symbol)
        self.assertIn("var", report)
        self.assertIn("cvar", report)

if __name__ == '__main__':
    unittest.main()