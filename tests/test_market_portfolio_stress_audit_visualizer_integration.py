import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_format(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_visualizer_integration_graphical_format(self):
        report_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(10.0, 500.0), 2)
        
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=None)
        result = visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)

if __name__ == "__main__":
    unittest.main()