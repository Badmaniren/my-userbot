import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_tail_risk_analyzer import market_portfolio_stress_tail_risk_analyzer
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class TestMarketPortfolioStressTailRiskAnalyzerIntegration(unittest.TestCase):

    def test_tail_risk_analyzer_integration(self):
        portfolio_id = str(uuid.uuid4())
        sim_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)

        mc_engine = market_portfolio_stress_monte_carlo_engine()
        sim_results = mc_engine.run_simulation(portfolio_id=portfolio_id, runs=sim_runs, confidence=confidence_level)

        self.assertIsNotNone(sim_results, "Monte Carlo engine должен вернуть результаты симуляции")

        analyzer = market_portfolio_stress_tail_risk_analyzer()
        tail_risk_metrics = analyzer.calculate_tail_risk(
            portfolio_id=portfolio_id,
            simulation_data=sim_results,
            confidence_level=confidence_level
        )

        self.assertIn("var", tail_risk_metrics, "Результат должен содержать Value at Risk (VaR)")
        self.assertIn("expected_shortfall", tail_risk_metrics, "Результат должен содержать Expected Shortfall (CVaR)")

        storage = db_storage()
        storage_key = f"tail_risk_{portfolio_id}"
        storage.save(storage_key, tail_risk_metrics)

        fetched_data = storage.load(storage_key)
        self.assertEqual(fetched_data.get("portfolio_id", portfolio_id), portfolio_id)
        self.assertAlmostEqual(fetched_data.get("confidence_level", confidence_level), confidence_level)

if __name__ == "__main__":
    unittest.main()