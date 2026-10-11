import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(1.0, 100.0), 2)
        self.tail_risk_metrics = {"var_95": round(random.uniform(-0.1, -0.01), 4), "cvar_95": round(random.uniform(-0.15, -0.05), 4)}

        self.visualizer = MarketPortfolioStressAuditVisualizer(
            db_storage="real_db_connection_mock",
            market_portfolio_stress_audit_summary_vault="vault_stub"
        )

    def test_visualize_text_summary_flow(self):
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

    def test_visualize_graphical_flow(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": self.tail_risk_metrics,
            "stream_payload": {"active_nodes": random.randint(1, 10)}
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["layout"], "graphical")
        self.assertEqual(result["adaptive_risk_score"], self.adaptive_risk_score)
        self.assertEqual(result["tail_risk_metrics"], self.tail_risk_metrics)
        self.assertIn("stream_payload", result)

    def test_invalid_payload_handling(self):
        random_string_payload = f"invalid_payload_{uuid.uuid4()}"
        result = market_portfolio_stress_audit_visualizer(random_string_payload)
        self.assertEqual(result, random_string_payload)

if __name__ == "__main__":
    unittest.main()