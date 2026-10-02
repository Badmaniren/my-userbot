import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_scenario_pipeline=None
        )

    def test_visualizer_text_summary_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_visualizer_graphical_format_integration(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical_chart",
            "adaptive_risk_score": self.adaptive_risk_score
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)

    def test_visualizer_empty_and_incorrect_dataset_resilience(self):
        random_payloads = [
            None,
            {},
            {"invalid_key": str(uuid.uuid4())},
            random.randint(1, 1000)
        ]
        
        for payload in random_payloads:
            result = self.visualizer.visualize(payload)
            if isinstance(payload, dict):
                self.assertIsNotNone(result)
            else:
                self.assertEqual(result, str(payload))

if __name__ == "__main__":
    unittest.main()