import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
import pickle

import skills.market_portfolio_monte_carlo as mpmc


class TestMarketPortfolioMonteCarlo(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: uuid.uuid4().hex
        self.rand_float = lambda: random.uniform(0.01, 0.99)
        self.portfolio_id = self.rand_str()
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=3))

    def test_monte_carlo_config_defaults(self):
        cfg = mpmc.MonteCarloConfig()
        self.assertEqual(cfg.num_simulations, 100)
        self.assertEqual(cfg.time_horizon, 30)
        self.assertEqual(cfg.confidence_level, 0.95)
        self.assertIsNone(cfg.random_seed)
        self.assertFalse(cfg.enable_slippage)

    def test_monte_carlo_result_to_dict(self):
        sim_id = self.rand_str()
        returns = [self.rand_float() for _ in range(5)]
        mean_ret = self.rand_float()
        median_ret = self.rand_float()
        var = self.rand_float()
        cvar = self.rand_float()
        max_dd = self.rand_float()
        percentiles = {"5%": self.rand_float()}
        metrics = {self.rand_str(): self.rand_str()}

        res = mpmc.MonteCarloResult(
            simulation_id=sim_id,
            returns=returns,
            mean_return=mean_ret,
            median_return=median_ret,
            var=var,
            cvar=cvar,
            max_drawdown=max_dd,
            percentiles=percentiles,
            metrics=metrics,
        )

        d = res.to_dict()
        self.assertEqual(d["simulation_id"], sim_id)
        self.assertEqual(d["returns"], returns)
        self.assertEqual(d["mean_return"], mean_ret)
        self.assertEqual(d["median_return"], median_ret)
        self.assertEqual(d["var"], var)
        self.assertEqual(d["cvar"], cvar)
        self.assertEqual(d["max_drawdown"], max_dd)
        self.assertEqual(d["percentiles"], percentiles)
        self.assertEqual(d["metrics"], metrics)

    def test_calculate_var_success(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        returns = sorted([random.gauss(0, 1) for _ in range(50)])
        val = engine.calculate_var(returns, 0.95)
        self.assertIsInstance(val, float)

    def test_calculate_var_invalid(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        with self.assertRaises(ValueError):
            engine.calculate_var([], 0.95)
        with self.assertRaises(ValueError):
            engine.calculate_var([0.1, 0.2], 1.5)

    def test_calculate_cvar_success(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        returns = sorted([random.gauss(0, 1) for _ in range(50)])
        val = engine.calculate_cvar(returns, 0.95)
        self.assertIsInstance(val, float)

    def test_calculate_cvar_invalid(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        with self.assertRaises(ValueError):
            engine.calculate_cvar([], 0.95)
        with self.assertRaises(ValueError):
            engine.calculate_cvar([0.1, 0.2], -0.1)

    def test_calculate_drawdown(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        trajectory = [100.0, 105.0, 90.0, 110.0]
        dd = engine.calculate_drawdown(trajectory)
        self.assertGreaterEqual(dd, 0.0)
        self.assertEqual(engine.calculate_drawdown([]), 0.0)

    def test_run_simulation_validation_errors(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        with self.assertRaises(ValueError):
            engine.run_simulation({"assets": []})
        with self.assertRaises(ValueError):
            engine.run_simulation({"assets": [{"weight": 1.0}], "total_value": -100})
        with self.assertRaises(ValueError):
            engine.run_simulation({"assets": [{"weight": 0.5}], "total_value": 100})

    def test_run_simulation_success(self):
        cfg = mpmc.MonteCarloConfig(num_simulations=10, time_horizon=5, random_seed=42)
        simulator_mock = MagicMock()
        simulator_mock.generate_scenarios.return_value = [
            {"asset_returns": {self.ticker: 0.05}} for _ in range(10)
        ]
        slippage_mock = MagicMock()
        slippage_mock.estimate_slippage.return_value = 0.001

        engine = mpmc.MarketPortfolioMonteCarlo(
            scenario_simulator=simulator_mock,
            slippage_model=slippage_mock,
            config=cfg
        )
        portfolio = {
            "assets": [{"ticker": self.ticker, "weight": 1.0}],
            "total_value": 10000.0
        }
        res = engine.run_simulation(portfolio)
        self.assertIsInstance(res, mpmc.MonteCarloResult)
        self.assertTrue(res.simulation_id.startswith("sim_"))
        self.assertEqual(len(res.returns), 10)

    def test_run_stress_scenario(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        portfolio = {"portfolio_id": self.portfolio_id}
        shock = -random.uniform(0.1, 0.5)
        res = engine.run_stress_scenario(portfolio, market_shock=shock)
        self.assertEqual(res["shock_factor"], shock)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertIn("stressed_var", res)
        self.assertIn("stressed_cvar", res)

    def test_export_results_json(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        res = mpmc.MonteCarloResult(
            simulation_id=self.rand_str(),
            returns=[0.1],
            mean_return=0.1,
            median_return=0.1,
            var=0.01,
            cvar=0.02,
            max_drawdown=0.05,
            percentiles={"5%": 0.01}
        )
        stream = io.StringIO()
        engine.export_results_json(res, stream)
        stream.seek(0)
        data = json.loads(stream.read())
        self.assertEqual(data["simulation_id"], res.simulation_id)

    def test_export_binary_report(self):
        engine = mpmc.MarketPortfolioMonteCarlo()
        res = mpmc.MonteCarloResult(
            simulation_id=self.rand_str(),
            returns=[0.2],
            mean_return=0.2,
            median_return=0.2,
            var=0.02,
            cvar=0.03,
            max_drawdown=0.04,
            percentiles={"5%": 0.02}
        )
        stream = io.BytesIO()
        engine.export_binary_report(res, stream)
        stream.seek(0)
        header = stream.read(11)
        self.assertEqual(header, b"MPMC_REPORT")
        payload = stream.read()
        decoded = pickle.loads(payload)
        self.assertEqual(decoded["simulation_id"], res.simulation_id)

    def test_functional_wrapper_with_db_storage(self):
        with patch("skills.market_portfolio_monte_carlo.db_storage") as mock_db:
            inp = {
                "portfolio_id": self.portfolio_id,
                "iterations": 15,
                "scenarios": [0.01, 0.02, 0.03, {"return": 0.04}, {"asset_returns": {self.ticker: 0.05}}]
            }
            res = mpmc.market_portfolio_monte_carlo(inp)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_id", res)
            self.assertIn("VaR_95", res)
            mock_db.assert_called_once()

    def test_functional_wrapper_dict_scenarios(self):
        with patch("skills.market_portfolio_monte_carlo.db_storage") as mock_db:
            inp = {
                "portfolio_id": self.portfolio_id,
                "iterations": 10,
                "scenarios": {"asset_returns": {self.ticker: 0.07}}
            }
            res = mpmc.market_portfolio_monte_carlo(inp)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            mock_db.assert_called_once()