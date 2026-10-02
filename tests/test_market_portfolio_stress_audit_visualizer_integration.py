import random
import unittest
import uuid

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.visualizer = MarketPortfolioStressAuditVisualizer()

    def test_text_summary_visualization_with_random_metrics(self):
        random_portfolio_id = f"portfolio_{uuid.uuid4().hex}"
        random_score = round(random.uniform(1.0, 99.9), 4)

        payload = {
            "portfolio_id": random_portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": random_score,
            "export_to_text_report": True,
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(random_portfolio_id, result)
        self.assertIn(str(random_score), result)
        self.assertIn("Exported to text report successfully", result)
        self.assertTrue(result.startswith("Portfolio Stress Audit Summary for"))

    def test_graphical_format_with_report_id_fallback(self):
        random_report_id = f"audit_rep_{uuid.uuid4().hex}"
        random_score = round(random.uniform(0.01, 10.0), 3)

        payload = {
            "report_id": random_report_id,
            "format": "graphical",
            "adaptive_risk_score": random_score,
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), random_score)

    def test_text_summary_without_optional_fields(self):
        random_portfolio_id = f"port_minimal_{uuid.uuid4().hex[:12]}"
        payload = {
            "portfolio_id": random_portfolio_id,
            "format": "text_summary",
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, str)
        self.assertIn(random_portfolio_id, result)
        self.assertNotIn("Adaptive Risk Score:", result)
        self.assertNotIn("Exported to text report successfully", result)

    def test_visualizer_initialization_with_dependencies(self):
        custom_storage_id = f"storage_{uuid.uuid4().hex}"
        visualizer_with_deps = MarketPortfolioStressAuditVisualizer(
            db_storage=custom_storage_id,
            extra_param=123,
        )

        self.assertEqual(visualizer_with_deps.db_storage, custom_storage_id)
        self.assertEqual(
            visualizer_with_deps.dependencies.get("extra_param"), 123
        )

        random_portfolio_id = f"port_dep_{uuid.uuid4().hex}"
        payload = {
            "portfolio_id": random_portfolio_id,
            "format": "dashboard_view",
        }
        result = visualizer_with_deps.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("status"), "success")

    def test_non_dict_payload_passthrough(self):
        random_raw_payload = f"raw_unstructured_audit_stream_{uuid.uuid4()}"
        result = market_portfolio_stress_audit_visualizer(random_raw_payload)

        self.assertIsInstance(result, str)
        self.assertEqual(result, random_raw_payload)


if __name__ == "__main__":
    unittest.main()