import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db_path = f"test_audit_storage_{uuid.uuid4().hex}.db"
        self.dependencies = {
            "db_storage": self.test_db_path,
            "market_portfolio_stress_audit_health_monitor": "active",
            "market_portfolio_stress_audit_summary_vault": "initialized"
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.dependencies)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_visualizer_integration_flow(self):
        portfolio_id = str(uuid.uuid4())
        risk_score = round(random.uniform(0.1, 0.99), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": risk_score,
            "tail_risk_metrics": {"var": random.random(), "cvar": random.random()},
            "stream_payload": {"status": "live_sync"}
        }

        result = self.visualizer.visualize(payload)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["adaptive_risk_score"], risk_score)
        self.assertIn("tail_risk_metrics", result)
        self.assertIn("stream_payload", result)

    def test_text_summary_generation_and_persistence(self):
        portfolio_id = str(uuid.uuid4())
        risk_score = round(random.uniform(10, 100), 1)
        
        payload = {
            "report_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": risk_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(risk_score), result)
        self.assertIn("Exported to text report successfully", result)

        with open(self.test_db_path, "w") as f:
            f.write(result)
        
        self.assertTrue(os.path.exists(self.test_db_path))
        with open(self.test_db_path, "r") as f:
            content = f.read()
            self.assertEqual(content, result)

if __name__ == "__main__":
    unittest.main()