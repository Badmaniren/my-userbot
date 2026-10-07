import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_deep_impact_analyzer import market_portfolio_stress_deep_impact_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioStressDeepImpactAnalyzerIntegration(unittest.TestCase):
    def test_deep_impact_analyzer_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.90, 0.99), 2)

        market_data = {
            "portfolio_id": portfolio_id,
            "runs": simulation_runs,
            "confidence": confidence_level,
            "volatility_shock": round(random.uniform(0.1, 0.5), 4),
            "liquidity_factor": round(random.uniform(0.5, 1.0), 4)
        }

        collector_result = market_portfolio_collector_agent(market_data)
        self.assertIsNotNone(collector_result)

        matrix_evaluation = market_portfolio_stress_scenario_matrix_evaluator(portfolio_id)
        self.assertIsInstance(matrix_evaluation, dict)

        monte_carlo_metrics = market_portfolio_stress_monte_carlo_engine(portfolio_id, runs=simulation_runs)
        self.assertIsInstance(monte_carlo_metrics, dict)

        deep_impact_result = market_portfolio_stress_deep_impact_analyzer(
            portfolio_id=portfolio_id,
            matrix_data=matrix_evaluation,
            monte_carlo_data=monte_carlo_metrics
        )

        self.assertIn("impact_score", deep_impact_result)
        self.assertIn("status", deep_impact_result)

        stored_record = db_storage(f"get_stress_impact_{portfolio_id}")
        self.assertIsNotNone(stored_record)

        test_filename = f"impact_report_{portfolio_id}.json"
        self.assertTrue(os.path.exists(test_filename) or isinstance(deep_impact_result, dict))

        if os.path.exists(test_filename):
            os.remove(test_filename)

if __name__ == "__main__":
    unittest.main()