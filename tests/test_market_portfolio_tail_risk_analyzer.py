import unittest
import os
import sys

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills'))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer, TailRiskAnalyzer


class TestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketPortfolioTailRiskAnalyzer()

    def test_calculate_var_cvar(self):
        returns = [-0.05, -0.04, -0.02, 0.01, 0.02, 0.03, 0.05]
        var = self.analyzer.calculate_var(returns, confidence_level=0.95)
        cvar = self.analyzer.calculate_cvar(returns, confidence_level=0.95)
        self.assertIsInstance(var, float)
        self.assertIsInstance(cvar, float)

    def test_calculate_tail_risk(self):
        market_data = {
            "portfolio_id": "test_p",
            "volatility": 0.2,
            "confidence_level": 0.95
        }
        metrics = self.analyzer.calculate_tail_risk(market_data)
        self.assertIn("var", metrics)
        self.assertIn("cvar", metrics)
        self.assertGreater(metrics["cvar"], 0)

    def test_compute_metrics(self):
        metrics = self.analyzer.compute_metrics("p123")
        self.assertIn("var", metrics)
        self.assertIn("cvar", metrics)


if __name__ == "__main__":
    unittest.main()
