import unittest
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_hedge_optimizer_core import (
    MarketPortfolioStressHedgeOptimizerCore,
    optimize_portfolio_hedge
)

class TestMarketPortfolioStressHedgeOptimizerCoreIntegration(unittest.TestCase):

    def test_optimizer_core_init_and_weights_valid(self):
        feed_id = uuid.uuid4().hex
        optimizer = MarketPortfolioStressHedgeOptimizerCore(data_feed=feed_id)
        self.assertEqual(optimizer.data_feed, feed_id)

        rand_key1 = uuid.uuid4().hex[:6]
        rand_key2 = uuid.uuid4().hex[:6]
        val1 = random.uniform(10.0, 100.0)
        val2 = random.uniform(100.0, 1000.0)
        portfolio = {rand_key1: val1, rand_key2: val2, "invalid": "string_val"}
        stress_matrix = [random.uniform(-0.1, 0.1) for _ in range(5)]

        weights = optimizer.calculate_hedge_weights(portfolio, stress_matrix)
        self.assertIn(rand_key1, weights)
        self.assertIn(rand_key2, weights)
        self.assertNotIn("invalid", weights)
        self.assertIsInstance(weights[rand_key1], float)

    def test_optimizer_core_weights_edge_cases(self):
        optimizer = MarketPortfolioStressHedgeOptimizerCore()

        with self.assertRaises(ValueError):
            optimizer.calculate_hedge_weights("not_a_dict", [])

        with self.assertRaises(ValueError):
            optimizer.calculate_hedge_weights({}, "not_a_list")

        res_empty = optimizer.calculate_hedge_weights({}, [])
        self.assertEqual(res_empty, {})

    def test_simulate_monte_carlo_stress(self):
        optimizer = MarketPortfolioStressHedgeOptimizerCore()
        init_val = random.uniform(1000.0, 5000.0)
        iters = random.randint(10, 50)

        sim_result = optimizer.simulate_monte_carlo_stress(init_val, iters)
        self.assertIn("final_median", sim_result)
        self.assertIn("iterations_run", sim_result)
        self.assertIn("path_sample", sim_result)
        self.assertEqual(sim_result["iterations_run"], iters)
        self.assertLessEqual(len(sim_result["path_sample"]), 5)

        with self.assertRaises(ValueError):
            optimizer.simulate_monte_carlo_stress(init_val, 0)

        with self.assertRaises(ValueError):
            optimizer.simulate_monte_carlo_stress(init_val, -5)

    def test_optimize_portfolio_hedge_integration(self):
        p_id = uuid.uuid4().hex
        k1 = uuid.uuid4().hex[:5]
        k2 = uuid.uuid4().hex[:5]
        v1 = random.uniform(50.0, 500.0)
        v2 = random.uniform(500.0, 5000.0)

        weights = {k1: v1, k2: v2}
        stress_data = {"scenario_impacts": [random.uniform(-0.5, 0.5) for _ in range(3)]}
        mc_metrics = {
            "var": random.uniform(-0.1, -0.01),
            "cvar": random.uniform(-0.2, -0.05)
        }

        result = optimize_portfolio_hedge(p_id, weights, stress_data, mc_metrics)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], p_id)
        self.assertIn("optimal_hedge_instruments", result)
        self.assertIn("expected_risk_reduction", result)
        self.assertIsInstance(result["expected_risk_reduction"], float)
        self.assertIn(k1, result["optimal_hedge_instruments"])
        self.assertIn(k2, result["optimal_hedge_instruments"])

    def test_optimize_portfolio_hedge_defaults(self):
        p_id = uuid.uuid4().hex
        weights = {uuid.uuid4().hex[:4]: random.uniform(10.0, 100.0)}
        stress_data = {}
        mc_metrics = {}

        result = optimize_portfolio_hedge(p_id, weights, stress_data, mc_metrics)
        self.assertEqual(result["portfolio_id"], p_id)
        self.assertIsInstance(result["expected_risk_reduction"], float)

if __name__ == "__main__":
    unittest.main()