import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_text_summary(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_risk_score,
            "export_to_text_report": True
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage="dummy_db")
        result_class = visualizer.visualize(payload)
        result_func = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIn(portfolio_id, result_class)
        self.assertIn(str(adaptive_risk_score), result_class)
        self.assertIn("Exported to text report successfully.", result_class)
        
        self.assertEqual(result_class, result_func)

    def test_visualizer_integration_graphical_format(self):
        report_id = str(uuid.uuid4())
        adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        tail_risk_metrics = {"var_95": random.uniform(-0.5, -0.1), "cvar_95": random.uniform(-0.8, -0.3)}
        stream_payload = {"channel": f"stream_{uuid.uuid4()}", "active": True}
        
        payload = {
            "report_id": report_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_risk_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }
        
        visualizer = MarketPortfolioStressAuditVisualizer()
        result_class = visualizer.visualize(payload)
        result_func = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result_class, dict)
        self.assertEqual(result_class.get("portfolio_id"), report_id)
        self.assertEqual(result_class.get("status"), "success")
        self.assertEqual(result_class.get("layout"), "graphical")
        self.assertEqual(result_class.get("adaptive_risk_score"), adaptive_risk_score)
        self.assertEqual(result_class.get("tail_risk_metrics"), tail_risk_metrics)
        self.assertEqual(result_class.get("stream_payload"), stream_payload)
        
        self.assertEqual(result_class, result_func)


if __name__ == "__main__":
    unittest.main()