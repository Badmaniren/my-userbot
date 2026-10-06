import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_mock_storage = {}
        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage=self.db_mock_storage
        )

    def test_text_summary_visualization_flow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 10.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        
        # Test direct function call
        result_func = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result_func)
        self.assertIn(str(adaptive_score), result_func)
        self.assertIn("Exported to text report successfully", result_func)
        
        # Test class instance call
        result_class = self.visualizer.visualize(payload)
        self.assertEqual(result_func, result_class)

    def test_graphical_visualization_flow(self):
        report_id = f"rep-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 10.0), 2)
        tail_risk = {"VaR_99": round(random.uniform(0.05, 0.35), 4), "ES_99": round(random.uniform(0.1, 0.5), 4)}
        stream_data = f"stream-chunk-{random.randint(1000, 9999)}"
        
        payload = {
            "report_id": report_id,
            "format": "graphical_dashboard",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk,
            "stream_payload": stream_data
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_non_dict_payload_fallback(self):
        random_raw_payload = f"raw-data-{uuid.uuid4()}"
        result = self.visualizer.visualize(random_raw_payload)
        self.assertEqual(result, random_raw_payload)

    def test_empty_and_missing_fields(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        result = self.visualizer.visualize(payload)
        self.assertIn(portfolio_id, result)
        self.assertNotIn("Adaptive Risk Score", result)
        self.assertNotIn("Exported to text report", result)

if __name__ == "__main__":
    unittest.main()