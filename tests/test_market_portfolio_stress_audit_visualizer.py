import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_db = uuid.uuid4().hex
        self.visualizer_class_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db)

    def test_init_stores_dependencies(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        instance = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(instance.dependencies.get(rand_key), rand_val)
        self.assertEqual(instance.db_storage, None)

        instance_with_db = MarketPortfolioStressAuditVisualizer(db_storage=rand_val)
        self.assertEqual(instance_with_db.db_storage, rand_val)

    def test_visualize_method_proxy(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_portfolio_id,
            "format": "text_summary"
        }
        res = self.visualizer_class_instance.visualize(payload)
        self.assertIn(rand_portfolio_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)

    def test_payload_not_dict_returns_str(self):
        rand_num = random.randint(1000, 99999)
        res = market_portfolio_stress_audit_visualizer(rand_num)
        self.assertEqual(res, str(rand_num))

        rand_str = uuid.uuid4().hex
        res_str = market_portfolio_stress_audit_visualizer(rand_str)
        self.assertEqual(res_str, rand_str)

    def test_text_summary_format_basic(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {rand_id}: Data successfully audited and visualized."
        self.assertEqual(result, expected)

    def test_text_summary_format_with_report_id(self):
        rand_report_id = uuid.uuid4().hex
        payload = {
            "report_id": rand_report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {rand_report_id}: Data successfully audited and visualized."
        self.assertEqual(result, expected)

    def test_text_summary_format_with_adaptive_score(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 99.9), 2)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, result)
        self.assertIn(str(rand_score), result)
        self.assertIn("Adaptive Risk Score:", result)

    def test_text_summary_format_with_export_to_text(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, result)
        self.assertIn("Exported to text report successfully.", result)

    def test_text_summary_format_full(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(10.0, 50.0), 4)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score,
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, result)
        self.assertIn(str(rand_score), result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_basic(self):
        rand_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": rand_format
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        expected = {
            "portfolio_id": rand_id,
            "status": "success",
            "layout": "graphical",
        }
        self.assertEqual(result, expected)

    def test_graphical_format_with_all_optional_fields(self):
        rand_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
        rand_score = random.randint(100, 999)
        rand_tail_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        rand_stream = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}

        payload = {
            "report_id": rand_id,
            "format": rand_format,
            "adaptive_risk_score": rand_score,
            "tail_risk_metrics": rand_tail_metrics,
            "stream_payload": rand_stream
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result.get("portfolio_id"), rand_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), rand_score)
        self.assertEqual(result.get("tail_risk_metrics"), rand_tail_metrics)
        self.assertEqual(result.get("stream_payload"), rand_stream)

    def test_io_bytes_simulation_integration(self):
        rand_binary_data = uuid.uuid4().bytes
        stream = io.BytesIO(rand_binary_data)
        read_content = stream.read()
        self.assertEqual(read_content, rand_binary_data)


if __name__ == "__main__":
    unittest.main()