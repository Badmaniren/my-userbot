import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)

class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_deps = {
            "".join(random.choices(string.ascii_lowercase, k=8)): uuid.uuid4().hex
            for _ in range(3)
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.random_deps)

    def test_init_stores_dependencies(self):
        self.assertEqual(self.visualizer.dependencies, self.random_deps)
        self.assertIsNone(self.visualizer.db_storage)

        db_val = uuid.uuid4().hex
        custom_vis = MarketPortfolioStressAuditVisualizer(db_storage=db_val)
        self.assertEqual(custom_vis.db_storage, db_val)

    def test_visualize_wrapper_delegates_correctly(self):
        random_payload = {
            "portfolio_id": uuid.uuid4().hex,
            "format": "text_summary",
            "adaptive_risk_score": random.uniform(1.0, 100.0)
        }
        with patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_func:
            mock_return = uuid.uuid4().hex
            mock_func.return_value = mock_return
            
            res = self.visualizer.visualize(random_payload)
            mock_func.assert_called_once_with(random_payload)
            self.assertEqual(res, mock_return)

    def test_non_dict_payload_returns_string(self):
        random_string = uuid.uuid4().hex
        res = market_portfolio_stress_audit_visualizer(random_string)
        self.assertEqual(res, random_string)

        random_int = random.randint(1000, 99999)
        res_int = market_portfolio_stress_audit_visualizer(random_int)
        self.assertEqual(res_int, str(random_int))

    def test_text_summary_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {portfolio_id}: Data successfully audited and visualized."
        self.assertEqual(res, expected)

    def test_text_summary_format_with_report_id_fallback(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {report_id}: Data successfully audited and visualized."
        self.assertEqual(res, expected)

    def test_text_summary_format_with_adaptive_score(self):
        portfolio_id = uuid.uuid4().hex
        score = round(random.uniform(0.0, 10.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {portfolio_id}: Data successfully audited and visualized. Adaptive Risk Score: {score}."
        self.assertEqual(res, expected)

    def test_text_summary_format_with_export_text(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {portfolio_id}: Data successfully audited and visualized. Exported to text report successfully."
        self.assertEqual(res, expected)

    def test_text_summary_format_comprehensive(self):
        portfolio_id = uuid.uuid4().hex
        score = round(random.uniform(10.0, 50.0), 4)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized. "
            f"Adaptive Risk Score: {score}. "
            f"Exported to text report successfully."
        )
        self.assertEqual(res, expected)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        format_type = "".join(random.choices(string.ascii_lowercase, k=6))
        while format_type == "text_summary":
            format_type = "".join(random.choices(string.ascii_lowercase, k=6))

        payload = {
            "portfolio_id": portfolio_id,
            "format": format_type
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = {
            "portfolio_id": portfolio_id,
            "status": "success",
            "layout": "graphical"
        }
        self.assertEqual(res, expected)

    def test_graphical_format_with_adaptive_score(self):
        portfolio_id = uuid.uuid4().hex
        score = round(random.uniform(50.0, 100.0), 3)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical_advanced",
            "adaptive_risk_score": score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        expected = {
            "portfolio_id": portfolio_id,
            "status": "success",
            "layout": "graphical",
            "adaptive_risk_score": score
        }
        self.assertEqual(res, expected)

if __name__ == "__main__":
    unittest.main()