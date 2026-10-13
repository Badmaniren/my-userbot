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
        self.rand_db_val = "".join(random.choices(string.ascii_letters, k=10))
        self.visualizer = MarketPortfolioStressAuditVisualizer(db_storage=self.rand_db_val)

    def test_init_and_storage(self):
        self.assertEqual(self.visualizer.db_storage, self.rand_db_val)
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        instance = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(instance.dependencies.get(rand_key), rand_val)

    def test_visualize_delegation(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio_id, "format": "text_summary"}
        result = self.visualizer.visualize(payload)
        self.assertIn(rand_portfolio_id, result)
        self.assertIsInstance(result, str)

    def test_non_dict_payload_returns_string(self):
        rand_int = random.randint(1000, 99999)
        result = market_portfolio_stress_audit_visualizer(rand_int)
        self.assertEqual(result, str(rand_int))

        rand_string = uuid.uuid4().hex
        result_str = market_portfolio_stress_audit_visualizer(rand_string)
        self.assertEqual(result_str, rand_string)

    def test_text_summary_format_basic(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)

    def test_text_summary_with_adaptive_score_and_export(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn(str(rand_score), res)
        self.assertIn("Exported to text report successfully", res)

    def test_graphical_format_basic(self):
        rand_id = uuid.uuid4().hex
        rand_format = "".join(random.choices(string.ascii_lowercase, k=6))
        payload = {
            "portfolio_id": rand_id,
            "format": rand_format
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), rand_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", res)
        self.assertNotIn("tail_risk_metrics", res)
        self.assertNotIn("stream_payload", res)

    def test_graphical_format_full_payload(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(0.1, 99.9), 4)
        rand_tail_metric = uuid.uuid4().hex
        rand_stream = uuid.uuid4().hex

        payload = {
            "portfolio_id": rand_id,
            "format": uuid.uuid4().hex,
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": rand_tail_metric,
            "stream_payload": rand_stream
        }

        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res.get("portfolio_id"), rand_id)
        self.assertEqual(res.get("adaptive_risk_score"), rand_score)
        self.assertEqual(res.get("tail_risk_metrics"), rand_tail_metric)
        self.assertEqual(res.get("stream_payload"), rand_stream)

    def test_stream_payload_bytes_io_mock(self):
        rand_bytes = uuid.uuid4().hex.encode('utf-8')
        stream_obj = io.BytesIO(rand_bytes)
        
        rand_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": "graphical",
            "stream_payload": stream_obj.read()
        }

        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res.get("stream_payload"), rand_bytes)


if __name__ == "__main__":
    unittest.main()