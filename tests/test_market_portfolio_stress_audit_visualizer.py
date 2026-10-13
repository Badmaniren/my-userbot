import unittest
from unittest.mock import patch
import random
import uuid
import string

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):
    def setUp(self):
        self.random_id = uuid.uuid4().hex
        self.random_score = round(random.uniform(1.0, 100.0), 2)
        self.random_metrics = {uuid.uuid4().hex: random.random() for _ in range(3)}
        self.random_stream = {uuid.uuid4().hex: ''.join(random.choices(string.ascii_letters, k=10))}

    def test_visualizer_class_initialization(self):
        db_mock = uuid.uuid4().hex
        visualizer = MarketPortfolioStressAuditVisualizer(db_storage=db_mock)
        self.assertEqual(visualizer.db_storage, db_mock)

    def test_visualizer_class_delegation(self):
        visualizer = MarketPortfolioStressAuditVisualizer()
        payload = {
            "portfolio_id": self.random_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score
        }
        res = visualizer.visualize(payload)
        self.assertIn(self.random_id, res)
        self.assertIn(str(self.random_score), res)

    def test_market_portfolio_stress_audit_visualizer_non_dict_payload(self):
        raw_string = uuid.uuid4().hex
        res = market_portfolio_stress_audit_visualizer(raw_string)
        self.assertEqual(res, raw_string)

    def test_text_summary_format_basic(self):
        payload = {
            "report_id": self.random_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)

    def test_text_summary_format_with_adaptive_score(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "text_summary",
            "adaptive_risk_score": self.random_score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_id, res)
        self.assertIn(str(self.random_score), res)
        self.assertIn("Adaptive Risk Score", res)

    def test_text_summary_format_with_export(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(self.random_id, res)
        self.assertIn("Exported to text report successfully", res)

    def test_graphical_format_basic(self):
        payload = {
            "portfolio_id": self.random_id,
            "format": "graphical"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res["portfolio_id"], self.random_id)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["layout"], "graphical")

    def test_graphical_format_extended_fields(self):
        payload = {
            "report_id": self.random_id,
            "format": "graphical",
            "adaptive_risk_score": self.random_score,
            "tail_risk_metrics": self.random_metrics,
            "stream_payload": self.random_stream
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(res["portfolio_id"], self.random_id)
        self.assertEqual(res["adaptive_risk_score"], self.random_score)
        self.assertEqual(res["tail_risk_metrics"], self.random_metrics)
        self.assertEqual(res["stream_payload"], self.random_stream)

    def test_external_module_integration_mock_safe(self):
        with patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_func:
            mock_res = uuid.uuid4().hex
            mock_func.return_value = mock_res
            visualizer = MarketPortfolioStressAuditVisualizer()
            payload = {"portfolio_id": self.random_id}
            res = visualizer.visualize(payload)
            self.assertEqual(res, mock_res)
            mock_func.assert_called_once_with(payload)