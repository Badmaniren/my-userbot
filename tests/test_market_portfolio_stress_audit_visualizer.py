import unittest
from unittest.mock import patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = f"PORT-{uuid.uuid4().hex[:8].upper()}"
        self.random_report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
        self.random_risk_score = round(random.uniform(1.0, 99.9), 2)
        self.random_compliance_status = random.choice(["APPROVED", "REJECTED", "PENDING_AUDIT"])
        self.random_tail_risk_metric = round(random.uniform(0.01, 0.99), 4)

        self.mock_dependencies = {
            "db_storage": f"db://cluster_{uuid.uuid4().hex[:6]}",
            "market_portfolio_audit_compliance_hub": f"hub://compliance_{uuid.uuid4().hex[:6]}",
            "market_portfolio_stress_scenario_pipeline": f"pipeline://stress_{uuid.uuid4().hex[:6]}"
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.mock_dependencies)

    def test_non_dict_payload_returns_string(self):
        random_string_payload = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        result = market_portfolio_stress_audit_visualizer(random_string_payload)
        self.assertIsInstance(result, str)
        self.assertEqual(result, random_string_payload)

    def test_text_summary_format_with_portfolio_id_and_adaptive_score(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_risk_score,
            "export_to_text_report": True
        }
        
        result = self.visualizer.visualize(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_portfolio_id, result)
        self.assertIn(str(self.random_risk_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_text_summary_format_with_report_id_fallback(self):
        payload = {
            "report_id": self.random_report_id,
            "format": "text_summary",
            "export_to_text_report": False
        }
        
        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.random_report_id, result)
        self.assertNotIn("Exported to text report successfully", result)

    def test_graphical_layout_format_returns_dict(self):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_risk_score,
            "tail_risk_metrics": {
                "var_99": self.random_tail_risk_metric,
                "compliance_status": self.random_compliance_status
            }
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.random_risk_score)
        self.assertIn("tail_risk_metrics", result)
        self.assertEqual(result["tail_risk_metrics"]["compliance_status"], self.random_compliance_status)

    def test_io_stream_handling_in_visualization_pipeline(self):
        random_bytes_content = f"audit_dump_{uuid.uuid4().hex}".encode("utf-8")
        stream = io.BytesIO(random_bytes_content)
        
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "format": "graphical",
            "stream_payload": stream.read().decode("utf-8")
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("stream_payload"), random_bytes_content.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()