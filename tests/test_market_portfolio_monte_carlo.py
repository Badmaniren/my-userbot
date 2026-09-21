import unittest
from unittest.mock import patch
import random
import uuid
import os
import tempfile
from skills.market_portfolio_monte_carlo import PortfolioMonteCarloSimulator, MonteCarloSimulator

class TestPortfolioMonteCarloSimulator(unittest.TestCase):
    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.rand_capital = float(random.randint(5000, 50000))
        self.rand_simulations = random.randint(10, 50)
        self.rand_days = random.randint(5, 15)
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.simulator = PortfolioMonteCarloSimulator(storage_filepath=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_alias_equality(self):
        self.assertIs(MonteCarloSimulator, PortfolioMonteCarloSimulator)

    def test_load_data_empty(self):
        res = self.simulator.load_data(uuid.uuid4().hex + ".json")
        self.assertEqual(res, {})

    @patch('skills.market_portfolio_monte_carlo.MarketPortfolioBacktester')
    def test_run_simulation_fallback_returns(self, mock_backtester_cls):
        mock_instance = mock_backtester_cls.return_value
        mock_instance.simulate_historical_trades.side_effect = Exception("Simulated failure")

        result = self.simulator.run_simulation(
            symbol=self.rand_symbol,
            initial_capital=self.rand_capital,
            simulations=self.rand_simulations,
            days=self.rand_days
        )

        self.assertIn("mean_final_value", result)
        self.assertIn("percentile_5", result)
        self.assertIn("percentile_95", result)
        self.assertIn("simulation_matrix", result)
        self.assertIn("mean_return", result)
        self.assertIn("var", result)
        self.assertIn("cvar", result)
        self.assertEqual(result["symbol"], self.rand_symbol)
        self.assertEqual(len(result["simulation_matrix"]), self.rand_simulations)

    @patch('skills.market_portfolio_monte_carlo.MarketPortfolioBacktester')
    def test_run_simulation_with_historical_data(self, mock_backtester_cls):
        mock_instance = mock_backtester_cls.return_value
        fake_returns = [random.uniform(-0.03, 0.04) for _ in range(10)]
        mock_instance.simulate_historical_trades.return_value = fake_returns

        result = self.simulator.run_simulation(
            symbol=self.rand_symbol,
            initial_capital=self.rand_capital,
            simulations=self.rand_simulations,
            days=self.rand_days
        )

        self.assertIsInstance(result["mean_final_value"], float)
        self.assertIsInstance(result["var"], float)
        self.assertIsInstance(result["cvar"], float)
        self.assertEqual(result["symbol"], self.rand_symbol)

    def test_calculate_var_cvar(self):
        fake_values = [self.rand_capital * (1.0 + random.uniform(-0.1, 0.1)) for _ in range(100)]
        var, cvar = self.simulator.calculate_var_cvar(fake_values, self.rand_capital, 0.95)
        self.assertIsInstance(var, float)
        self.assertIsInstance(cvar, float)
        self.assertGreaterEqual(cvar, var)

    @patch.object(PortfolioMonteCarloSimulator, 'run_simulation')
    def test_generate_monte_carlo_report(self, mock_run_sim):
        rand_mean = float(random.randint(1000, 99999))
        mock_run_sim.return_value = {
            "mean_final_value": rand_mean,
            "percentile_5": rand_mean * 0.9,
            "percentile_95": rand_mean * 1.1,
            "simulation_matrix": [rand_mean],
            "mean_return": 0.05,
            "var": 100.0,
            "cvar": 120.0,
            "symbol": self.rand_symbol
        }

        report = self.simulator.generate_monte_carlo_report(
            symbol=self.rand_symbol,
            days=self.rand_days,
            simulations=self.rand_simulations,
            initial_capital=self.rand_capital
        )

        self.assertEqual(report["symbol"], self.rand_symbol)
        self.assertEqual(report["mean_final_value"], rand_mean)
        mock_run_sim.assert_called_once_with(
            symbol=self.rand_symbol,
            initial_capital=self.rand_capital,
            simulations=self.rand_simulations,
            days=self.rand_days
        )
