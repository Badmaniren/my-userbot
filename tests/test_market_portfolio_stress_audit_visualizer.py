import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer, start_new

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.random_id = uuid.uuid4().hex
        self.random_score = random.uniform(0.1, 99.9)
        self.random_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        self.random_stream = uuid.uuid4().hex
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=MagicMock())

    def test_visualize_text_summary_integrity(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score,
            "export_to_text_report": True
        }

        result = self.visualizer.visualize(payload)

        self.assertIn(self.random_id, result)
        self.assertIn(str(self.random_score), result)
        self.assertTrue(result.endswith("Exported to text report successfully."))

    def test_visualize_graphical_format_structure(self):
        payload = {
            "report_id": self.random_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_score,
            "tail_risk_metrics": self.random_metrics,
            "stream_payload": self.random_stream
        }

        result = self.visualizer.visualize(payload)

        self.assertEqual(result["portfolio_id"], self.random_id)
        self.assertEqual(result["adaptive_risk_score"], self.random_score)
        self.assertEqual(result["tail_risk_metrics"], self.random_metrics)
        self.assertEqual(result["stream_payload"], self.random_stream)
        self.assertEqual(result["layout"], "graphical")

    def test_invalid_payload_handling(self):
        random_garbage = "".join(random.choices(string.ascii_letters, k=10))
        result = market_portfolio_stress_audit_visualizer(random_garbage)
        self.assertEqual(result, random_garbage)

    def test_missing_optional_fields(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "graphical"
        }
        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertEqual(result["status"], "success")

    def test_stream_processing_simulation(self):
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)
        payload = {
            "portfolio_id": self.random_id,
            "format": "graphical",
            "stream_payload": mock_stream
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result["stream_payload"], random_bytes)

    def test_id_fallback_logic(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)

    def test_render_audit_dashboard(self):
        res = self.visualizer.render_audit_dashboard({"portfolio_id": self.random_id, "metrics": {"var": 0.05}})
        self.assertEqual(res["portfolio_id"], self.random_id)
        self.assertEqual(res["audit_verdict"], "PASSED")
        self.assertEqual(res["status"], "success")

    def test_start_new_factory(self):
        inst = start_new({"db_storage": "mock_db"})
        self.assertIsInstance(inst, MarketPortfolioStressAuditVisualizer)

if __name__ == '__main__':
    unittest.main()