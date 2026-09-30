import unittest
import uuid
import random
import io
from skills.market_portfolio_drawdown_analyzer import MarketPortfolioDrawdownAnalyzer, market_portfolio_drawdown_analyzer

class TestMarketPortfolioDrawdownAnalyzerIntegration(unittest.TestCase):
    def test_analyze_drawdown_integration(self):
        portfolio_id = str(uuid.uuid4())
        confidence = round(random.uniform(0.90, 0.99), 2)

        analyzer = MarketPortfolioDrawdownAnalyzer()
        result = analyzer.analyze_drawdown(portfolio_id, confidence=confidence)

        self.assertIn("max_drawdown", result)
        self.assertIn("value_at_risk", result)
        self.assertIn("conditional_var", result)
        self.assertIsInstance(result["max_drawdown"], float)
        self.assertGreaterEqual(result["max_drawdown"], 0.0)

    def test_compute_risk_metrics_integration(self):
        alpha = round(random.uniform(0.90, 0.99), 2)
        random_returns = [round(random.uniform(-0.05, 0.05), 4) for _ in range(5)]
        stream_data = f"returns:{','.join(map(str, random_returns))}"
        payload_stream = io.BytesIO(stream_data.encode('utf-8'))

        analyzer = MarketPortfolioDrawdownAnalyzer()
        result = analyzer.compute_risk_metrics(payload_stream, alpha=alpha)

        self.assertIn("value_at_risk", result)
        self.assertIn("conditional_var", result)
        self.assertIsInstance(result["value_at_risk"], float)
        self.assertIsInstance(result["conditional_var"], float)

    def test_evaluate_stress_scenario_integration(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = f"stress_test_{uuid.uuid4().hex[:8]}"

        analyzer = MarketPortfolioDrawdownAnalyzer()
        result = analyzer.evaluate_stress_scenario(portfolio_id, scenario_name)

        self.assertIn("scenario", result)
        self.assertEqual(result["scenario"], scenario_name)
        self.assertIn("simulated_max_drawdown", result)

    def test_monitor_tail_risks_integration(self):
        portfolio_id = str(uuid.uuid4())
        analyzer = MarketPortfolioDrawdownAnalyzer()
        result = analyzer.monitor_tail_risks(portfolio_id)

        self.assertIn("anomaly_detected", result)
        self.assertIn("anomaly_score", result)
        self.assertIsInstance(result["anomaly_detected"], bool)

    def test_functional_wrapper_integration(self):
        shock_factor = round(random.uniform(0.1, 0.5), 2)
        portfolio_id = str(uuid.uuid4())
        payload = {
            "portfolio_id": portfolio_id,
            "simulation_data": {
                "shock_factor": shock_factor
            }
        }

        result = market_portfolio_drawdown_analyzer(payload)

        self.assertIn("max_drawdown", result)
        self.assertEqual(result["max_drawdown"], float(shock_factor))
        self.assertIn("value_at_risk", result)
        self.assertIn("conditional_var", result)

if __name__ == '__main__':
    unittest.main()