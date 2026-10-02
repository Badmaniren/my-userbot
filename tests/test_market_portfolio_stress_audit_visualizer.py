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
        self.random_db = uuid.uuid4().hex
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.random_db)

    def test_init_and_dependencies(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        vis = MarketPortfolioStressAuditVisualizer(**{rand_key: rand_val})
        self.assertEqual(vis.dependencies.get(rand_key), rand_val)
        self.assertEqual(vis.db_storage, vis.dependencies.get("db_storage"))

    def test_visualize_method_delegation(self):
        rand_portfolio = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio, "format": "text_summary"}
        res_direct = market_portfolio_stress_audit_visualizer(payload)
        res_instance = self.visualizer_instance.visualize(payload)
        self.assertEqual(res_direct, res_instance)
        self.assertIn(rand_portfolio, res_instance)

    def test_non_dict_payload(self):
        rand_string = ''.join(random.choices(string.ascii_letters, k=16))
        res = market_portfolio_stress_audit_visualizer(rand_string)
        self.assertEqual(res, rand_string)

        rand_number = random.randint(1000, 99999)
        res_num = market_portfolio_stress_audit_visualizer(rand_number)
        self.assertEqual(res_num, str(rand_number))

    def test_text_summary_format_basic(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn("Portfolio Stress Audit Summary", res)
        self.assertIn("Data successfully audited and visualized.", res)

    def test_text_summary_with_report_id_fallback(self):
        rand_report = uuid.uuid4().hex
        payload = {
            "report_id": rand_report,
            "format": "text_summary"
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_report, res)

    def test_text_summary_with_adaptive_score(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(1.0, 99.9), 2)
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "adaptive_risk_score": rand_score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn(f"Adaptive Risk Score: {rand_score}.", res)

    def test_text_summary_with_export_text(self):
        rand_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": rand_id,
            "format": "text_summary",
            "export_to_text_report": True
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(rand_id, res)
        self.assertIn("Exported to text report successfully.", res)

    def test_graphical_format_basic(self):
        rand_id = uuid.uuid4().hex
        rand_format = uuid.uuid4().hex
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

    def test_graphical_format_with_adaptive_score(self):
        rand_id = uuid.uuid4().hex
        rand_score = round(random.uniform(10.0, 50.0), 4)
        payload = {
            "portfolio_id": rand_id,
            "format": "graphical_chart",
            "adaptive_risk_score": rand_score
        }
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), rand_id)
        self.assertEqual(res.get("adaptive_risk_score"), rand_score)
        self.assertEqual(res.get("status"), "success")

    def test_empty_or_malformed_payload_resilience(self):
        payload = {}
        res = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn("Portfolio Stress Audit Summary for None", res)

        payload_weird_types = {
            "portfolio_id": None,
            "format": "text_summary",
            "adaptive_risk_score": None,
            "export_to_text_report": None
        }
        res_weird = market_portfolio_stress_audit_visualizer(payload_weird_types)
        self.assertIn("Portfolio Stress Audit Summary for None", res_weird)
        self.assertNotIn("Adaptive Risk Score", res_weird)
        self.assertNotIn("Exported to text report", res_weird)

if __name__ == "__main__":
    unittest.main()