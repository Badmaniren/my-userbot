import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.dependencies = {
            "db_storage": None,
            "market_portfolio_stress_monte_carlo_engine": None,
            "market_portfolio_stress_reporter": None
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.dependencies)

    def test_visualize_text_summary_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }
        
        result_class = self.visualizer.visualize(payload)
        result_func = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIn(self.portfolio_id, result_class)
        self.assertIn(str(self.adaptive_risk_score), result_class)
        self.assertIn("Exported to text report successfully.", result_class)
        
        self.assertEqual(result_class, result_func)

    def test_visualize_graphical_format_integration(self):
        report_id = str(uuid.uuid4())
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)

if __name__ == "__main__":
    unittest.main()