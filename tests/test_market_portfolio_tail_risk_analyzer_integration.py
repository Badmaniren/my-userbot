import unittest
import uuid
import random
from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer, TailRiskAnalyzer
from skills import market_portfolio_collector_agent
from skills.db_storage import DBStorage


class TestMarketPortfolioTailRiskAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=self.db)
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"

    def test_calculate_risk_metrics_integration(self):
        random_returns = [round(random.uniform(-0.05, 0.05), 4) for _ in range(50)]

        if hasattr(self.db, 'save_portfolio_history'):
            self.db.save_portfolio_history(self.portfolio_id, random_returns)
        elif hasattr(self.db, 'save_portfolio'):
            self.db.save_portfolio(self.portfolio_id, random_returns)

        metrics = self.analyzer.calculate_risk_metrics(self.portfolio_id, confidence_level=0.95)

        self.assertIn('var', metrics)
        self.assertIn('cvar', metrics)
        self.assertIsInstance(metrics['var'], float)
        self.assertIsInstance(metrics['cvar'], float)

        base_analyzer = TailRiskAnalyzer()
        expected_var = base_analyzer.calculate_var(random_returns, confidence_level=0.95)
        self.assertEqual(metrics['var'], expected_var)

    def test_analyze_method_integration(self):
        random_returns = [round(random.uniform(-0.03, 0.04), 4) for _ in range(30)]

        if hasattr(market_portfolio_collector_agent, 'save_historical_returns'):
            market_portfolio_collector_agent.save_historical_returns(self.portfolio_id, random_returns)
        elif hasattr(self.db, 'save_portfolio_history'):
            self.db.save_portfolio_history(self.portfolio_id, random_returns)

        try:
            result = self.analyzer.analyze(self.portfolio_id)
            self.assertIn('var', result)
            self.assertIn('cvar', result)
        except Exception as e:
            self.fail(f"Analyze method failed due to integration issue: {e}")


if __name__ == '__main__':
    unittest.main()
