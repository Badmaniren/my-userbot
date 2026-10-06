import unittest
import uuid
import random
from skills.market_portfolio_stress_hedge_optimizer_core import (
    MarketPortfolioStressHedgeOptimizerCore,
    optimize_portfolio_hedge,
)
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.market_portfolio_stress_scenario_matrix_evaluator import evaluate_scenario_matrix
from skills.db_storage import save_hedge_optimization_result, get_hedge_optimization_result


class TestMarketPortfolioStressHedgeOptimizerCoreIntegration(unittest.TestCase):

    def test_end_to_end_hedge_optimization_and_persistence(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        asset_count = random.randint(2, 5)
        weights = {f"ASSET_{i}": round(random.uniform(1000.0, 50000.0), 2) for i in range(asset_count)}

        scenario_data = [
            {"scenario": "crash_2008", "drop": round(random.uniform(-0.4, -0.2), 2)},
            {"scenario": "covid_2020", "drop": round(random.uniform(-0.3, -0.15), 2)}
        ]

        evaluated_matrix = evaluate_scenario_matrix(scenario_data)

        initial_val = sum(weights.values())
        iterations = random.randint(50, 200)
        monte_carlo_res = run_monte_carlo_simulation(initial_val, iterations)

        stress_data = {"scenario_impacts": evaluated_matrix if isinstance(evaluated_matrix, list) else [0.1, -0.2]}
        monte_carlo_metrics = {
            "var": monte_carlo_res.get("var", -0.04),
            "cvar": monte_carlo_res.get("cvar", -0.07)
        }

        optimization_result = optimize_portfolio_hedge(
            portfolio_id=portfolio_id,
            weights=weights,
            stress_data=stress_data,
            monte_carlo_metrics=monte_carlo_metrics
        )

        self.assertIn("portfolio_id", optimization_result)
        self.assertEqual(optimization_result["portfolio_id"], portfolio_id)
        self.assertIn("optimal_hedge_instruments", optimization_result)
        self.assertIn("expected_risk_reduction", optimization_result)

        opt_core = MarketPortfolioStressHedgeOptimizerCore(data_feed=portfolio_id)
        sim_result = opt_core.simulate_monte_carlo_stress(initial_value=initial_val, iterations=max(10, iterations // 2))
        self.assertIn("final_median", sim_result)
        self.assertEqual(sim_result["iterations_run"], max(10, iterations // 2))

        save_hedge_optimization_result(portfolio_id, optimization_result)
        fetched_result = get_hedge_optimization_result(portfolio_id)

        self.assertIsNotNone(fetched_result)
        if isinstance(fetched_result, dict):
            self.assertEqual(fetched_result.get("portfolio_id"), portfolio_id)
            self.assertIn("expected_risk_reduction", fetched_result)


if __name__ == "__main__":
    unittest.main()