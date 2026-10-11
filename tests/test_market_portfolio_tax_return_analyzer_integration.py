import unittest
import uuid
import random
from skills.market_portfolio_tax_return_analyzer import PortfolioTaxReturnAnalyzer, analyze_portfolio_tax_return
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator

class TestPortfolioTaxReturnAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.symbol = random.choice(["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"])
        self.analyzer = PortfolioTaxReturnAnalyzer()

    def test_analyze_portfolio_tax_return_integration(self):
        result = self.analyzer.analyze_portfolio_tax_return(
            portfolio_id=self.portfolio_id,
            symbol=self.symbol
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("total_return", result)
        self.assertIn("tax_drag", result)
        self.assertIn("after_tax_return", result)

        total_return = result.get("total_return", 0.0)
        tax_drag = result.get("tax_drag", 0.0)
        after_tax_return = result.get("after_tax_return", 0.0)

        self.assertAlmostEqual(after_tax_return, total_return - tax_drag)

    def test_evaluate_tax_efficiency_integration(self):
        result = self.analyzer.evaluate_tax_efficiency(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            symbol=self.symbol
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("deals_evaluated", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("tax_data", result)

    def test_process_strategy_dividends_integration(self):
        mock_stream = {
            "stream_id": uuid.uuid4().hex,
            "dividends": [random.uniform(10.0, 500.0) for _ in range(3)]
        }
        result = self.analyzer.process_strategy_dividends(mock_stream)
        self.assertIsInstance(result, dict)

    def test_functional_helper_integration(self):
        perf_data = {"total_return": random.uniform(100.0, 1000.0)}
        tax_data = {"tax_drag": random.uniform(10.0, 150.0), "tax_efficiency_score": 0.85}

        result = analyze_portfolio_tax_return(
            portfolio_id=self.portfolio_id,
            performance_data=perf_data,
            tax_data=tax_data
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("total_return"), perf_data["total_return"])
        self.assertEqual(result.get("tax_drag"), tax_data["tax_drag"])
        self.assertEqual(result.get("tax_efficiency_score"), tax_data["tax_efficiency_score"])
        self.assertAlmostEqual(
            result.get("after_tax_return"),
            perf_data["total_return"] - tax_data["tax_drag"]
        )

if __name__ == "__main__":
    unittest.main()