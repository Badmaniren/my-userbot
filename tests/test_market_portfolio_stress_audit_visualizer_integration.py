import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_summary(self):
        portfolio_id_val = f"portfolio-{uuid.uuid4()}"
        payload = {
            "portfolio_id": portfolio_id_val,
            "format": "text_summary",
            "metric_value": random.uniform(100.0, 10000.0)
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id_val, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_visualizer_integration_graphical(self):
        report_id_val = f"report-{uuid.uuid4()}"
        payload = {
            "report_id": report_id_val,
            "format": "graphical",
            "stress_factor": random.randint(1, 100)
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id_val)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")

    def test_visualizer_integration_invalid_payload_fallback(self):
        random_payload = f"raw-string-{uuid.uuid4()}"
        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(random_payload)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, random_payload)

if __name__ == "__main__":
    unittest.main()