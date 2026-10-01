import unittest
import uuid
import random
from datetime import datetime

from skills.market_portfolio_var_trend_analyzer import analyze_var_and_stress_trends
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress
from skills.market_portfolio_scenario_simulator import simulate_market_scenario
from skills.db_storage import save_trend_analysis_result, get_trend_analysis_result


class TestMarketPortfolioVarTrendAnalyzerIntegration(unittest.TestCase):

    def test_var_trend_analyzer_end_to_end_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        run_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.95, 0.99), 4)
        horizon_days = random.randint(5, 30)

        market_shock_factor = round(random.uniform(-0.15, -0.02), 4)
        simulation_seed = random.randint(1000, 99999)

        monte_carlo_output = run_monte_carlo_stress(
            portfolio_id=portfolio_id,
            simulation_seed=simulation_seed,
            shock_factor=market_shock_factor,
            iterations=500
        )

        self.assertIsNotNone(monte_carlo_output)
        self.assertIn("stress_var", monte_carlo_output)

        scenario_output = simulate_market_scenario(
            portfolio_id=portfolio_id,
            horizon=horizon_days,
            stress_metrics=monte_carlo_output
        )

        self.assertIsNotNone(scenario_output)

        trend_analysis_output = analyze_var_and_stress_trends(
            run_id=run_id,
            portfolio_id=portfolio_id,
            confidence=confidence_level,
            historical_window_days=horizon_days,
            scenario_data=scenario_output
        )

        self.assertIsNotNone(trend_analysis_output)
        self.assertEqual(trend_analysis_output.get("run_id"), run_id)
        self.assertEqual(trend_analysis_output.get("portfolio_id"), portfolio_id)
        self.assertIn("trend_slope", trend_analysis_output)
        self.assertIn("risk_velocity", trend_analysis_output)

        save_success = save_trend_analysis_result(trend_analysis_output)
        self.assertTrue(save_success)

        persisted_data = get_trend_analysis_result(run_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data["portfolio_id"], portfolio_id)
        self.assertEqual(persisted_data["trend_slope"], trend_analysis_output["trend_slope"])


if __name__ == "__main__":
    unittest.main()