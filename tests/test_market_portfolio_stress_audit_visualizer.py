import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.db_mock = MagicMock()
        self.random_deps = {
            "db_storage": self.db_mock,
            f"extractor_tool_{random.randint(100000, 999999)}": ''.join(random.choices(string.ascii_letters, k=10)),
            "market_portfolio_backtester": MagicMock()
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_and_dependencies(self):
        self.assertEqual(self.visualizer.db_storage, self.db_mock)
        self.assertEqual(self.visualizer.dependencies, self.random_deps)

    def test_payload_not_dict_returns_string(self):
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        result = market_portfolio_stress_audit_visualizer(random_string)
        self.assertIsInstance(result, str)
        self.assertEqual(result, random_string)

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertIn("Data successfully audited and visualized.", result)

    def test_text_summary_format_with_adaptive_score(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(1.0, 100.0), 2)
        payload = {
            "report_id": report_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)
        self.assertIn(f"Adaptive Risk Score: {adaptive_score}.", result)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn("Exported to text report successfully.", result)

    def test_graphical_format_default(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": ''.join(random.choices(string.ascii_lowercase, k=8))
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_full_payload(self):
        report_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(0.01, 99.99), 4)
        tail_risk_metrics = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.random()
            for _ in range(3)
        }
        stream_payload = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.randint(1, 100)
            for _ in range(2)
        }
        
        payload = {
            "report_id": report_id,
            "format": "graphical_custom",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": tail_risk_metrics,
            "stream_payload": stream_payload
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("tail_risk_metrics"), tail_risk_metrics)
        self.assertEqual(result.get("stream_payload"), stream_payload)

    def test_visualizer_class_method_delegation(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        res_from_instance = self.visualizer.visualize(payload)
        res_from_func = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res_from_instance, res_from_func)
        self.assertIn(portfolio_id, res_from_instance)