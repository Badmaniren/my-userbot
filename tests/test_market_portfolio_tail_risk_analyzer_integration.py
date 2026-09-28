import unittest
import os
import sys

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills'))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer


class TestMarketPortfolioTailRiskAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketPortfolioTailRiskAnalyzer()

    def test_tail_risk_integration(self):
        market_data = {
            "portfolio_id": "integration_p1",
            "volatility": 0.25,
            "confidence_level": 0.95
        }
        res = self.analyzer.calculate_tail_risk(market_data)
        self.assertIn("var", res)
        self.assertIn("cvar", res)
        self.assertEqual(res["var"], round(0.25 * 1.645, 4))


if __name__ == "__main__":
    unittest.main()
