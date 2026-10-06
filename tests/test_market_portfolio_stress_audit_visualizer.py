import unittest
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_db_val = uuid.uuid4().hex
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db_val)

    def test_init_and_dependencies(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        inst = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(inst.dependencies.get(rand_key), rand_val)
        self.assertEqual(inst.db_storage, None)

        inst_with_db = MarketPortfolioStressAuditVisualizer(db_storage=rand_val)
        self.assertEqual(inst_with_db.db_storage, rand_val)

    def test_visualize_wrapper_delegation(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary"
        }
        res = self.visualizer.visualize(payload)
        self.assertIn(rand_portfolio_id, res)

    def test_payload_not_dict_returns_string(self):
        rand_int = random.randint(100000, 999999)
        res = market_portfolio_stress_audit_visualizer(rand_int)
        self.assertEqual(res, str(rand_int))

        rand_str = uuid.uuid4().hex
        res_str = market_portfolio_stress_audit_visualizer(rand_str)
        self.assertEqual(res_str, rand_str)

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)

    def test_text_summary_with_report_id_fallback(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)

    def test_text_summary_with_adaptive_score(self):
        portfolio_id = uuid.uuid4().hex
        score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(str(score), result)
        self.assertIn("Adaptive Risk Score", result)

    def test_text_summary_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        format_type = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_with_all_optional_fields(self):
        portfolio_id = uuid.uuid4().hex
        format_type = uuid.uuid4().hex
        score = round(random.uniform(-50.0, 50.0), 4)
        tail_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        stream_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}

        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type,
            "adaptive_risk_score": score,
            "tail_risk_metrics": tail_metrics,
            "stream_payload": stream_data
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("adaptive_risk_score"), score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_metrics)
        self.assertEqual(result.get("stream_payload"), stream_data)

    def test_stream_io_integration_mock(self):
        rand_bytes = uuid.uuid4().bytes
        stream_io = io.BytesIO(rand_bytes)
        portfolio_id = uuid.uuid4().hex
        
        payload = {
            "portfolio_id": portfolio_id,
            "format": uuid.uuid4().hex,
            "stream_payload": stream_io.read()
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("stream_payload"), rand_bytes)


if __name__ == "__main__":
    unittest.main()