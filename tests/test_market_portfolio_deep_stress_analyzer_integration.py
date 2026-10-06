import unittest
import uuid
import random
from skills.market_portfolio_deep_stress_analyzer import MarketPortfolioDeepStressAnalyzer, StressAnalysisError
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
from skills.market_portfolio_stress_reporter import MarketPortfolioStressReporter
from skills.market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore
from skills.db_storage import DBStorage

class TestMarketPortfolioDeepStressAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_storage = DBStorage()
        self.monte_carlo = MarketPortfolioStressMonteCarloEngine()
        self.reporter = MarketPortfolioStressReporter()
        self.simulator = MarketPortfolioStressScenarioPipeline()
        self.var_core = MarketPortfolioVarLiquidityCore()

        self.analyzer = MarketPortfolioDeepStressAnalyzer(
            db_storage=self.db_storage,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo,
            market_portfolio_stress_reporter=self.reporter,
            market_portfolio_scenario_simulator=self.simulator,
            market_portfolio_var_liquidity_core=self.var_core
        )

    def test_analyze_portfolio_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        simulations = random.randint(100, 1000)
        confidence = round(random.uniform(0.90, 0.99), 2)

        try:
            result = self.analyzer.analyze_portfolio(
                portfolio_id=portfolio_id,
                simulations=simulations,
                confidence=confidence
            )
        except Exception as e:
            self.fail(f"Integration analysis failed unexpectedly with real modules: {str(e)}")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("analysis_id", result)
        self.assertIn("monte_carlo_results", result)
        self.assertIn("var_results", result)
        self.assertIn("report", result)
        self.assertIsInstance(result["analysis_id"], str)

    def test_perform_deep_analysis_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        metrics = {"risk_score": random.random(), "exposure": random.randint(1000, 50000)}
        raw_data = {"raw_points": [random.randint(1, 100) for _ in range(5)]}

        result = self.analyzer.perform_deep_analysis(
            portfolio_id=portfolio_id,
            metrics=metrics,
            raw_data=raw_data
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["metrics"], metrics)
        self.assertIn("report_id", result)
        self.assertTrue(result["report_id"].startswith("rep_"))
        self.assertEqual(result["status"], "processed")

if __name__ == "__main__":
    unittest.main()