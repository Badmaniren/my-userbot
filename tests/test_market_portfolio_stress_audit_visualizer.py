import io
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)


def _generate_random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _generate_random_score():
    return round(random.uniform(0.01, 100.0), 3)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def test_non_dict_payload_returns_string_representation(self):
        non_dict_inputs = [
            uuid.uuid4().hex,
            random.randint(10000, 99999),
            random.uniform(1.0, 500.0),
            [uuid.uuid4().hex, random.randint(1, 100)],
            None,
            False,
        ]
        for payload in non_dict_inputs:
            result = market_portfolio_stress_audit_visualizer(payload)
            self.assertEqual(result, str(payload))

    def test_text_summary_default_minimal_portfolio_id(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        payload = {"portfolio_id": portfolio_id}

        result = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {portfolio_id}: Data successfully audited and visualized."
        self.assertEqual(result, expected)

    def test_text_summary_fallback_to_report_id(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        payload = {"report_id": report_id}

        result = market_portfolio_stress_audit_visualizer(payload)
        expected = f"Portfolio Stress Audit Summary for {report_id}: Data successfully audited and visualized."
        self.assertEqual(result, expected)

    def test_text_summary_with_adaptive_risk_score(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        score = _generate_random_score()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        expected = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized. Adaptive Risk Score: {score}."
        )
        self.assertEqual(result, expected)

    def test_text_summary_with_export_to_text_report(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        expected = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized. Exported to text report successfully."
        )
        self.assertEqual(result, expected)

    def test_text_summary_complete_flags(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        score = _generate_random_score()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
            "export_to_text_report": True,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        expected = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized. "
            f"Adaptive Risk Score: {score}. Exported to text report successfully."
        )
        self.assertEqual(result, expected)

    def test_graphical_format_without_score(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        custom_format = f"graph_{uuid.uuid4().hex[:8]}"
        payload = {
            "portfolio_id": portfolio_id,
            "format": custom_format,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)

    def test_graphical_format_with_adaptive_risk_score(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        score = _generate_random_score()
        custom_format = f"dashboard_{uuid.uuid4().hex[:6]}"
        payload = {
            "report_id": report_id,
            "format": custom_format,
            "adaptive_risk_score": score,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), score)

    def test_class_initialization_dependencies(self):
        mock_storage = MagicMock()
        random_key = f"key_{_generate_random_string(8)}"
        random_val = f"val_{_generate_random_string(8)}"
        kwargs = {
            "db_storage": mock_storage,
            random_key: random_val,
        }

        visualizer = MarketPortfolioStressAuditVisualizer(**kwargs)
        self.assertEqual(visualizer.db_storage, mock_storage)
        self.assertIn(random_key, visualizer.dependencies)
        self.assertEqual(visualizer.dependencies[random_key], random_val)

    def test_class_visualize_delegation(self):
        random_key = f"dep_{_generate_random_string(6)}"
        visualizer = MarketPortfolioStressAuditVisualizer(**{random_key: uuid.uuid4().hex})

        portfolio_id = f"port_{uuid.uuid4().hex}"
        score = _generate_random_score()
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score,
        }

        with patch(
            "skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer"
        ) as mock_func:
            sentinel_result = f"audit_result_{uuid.uuid4().hex}"
            mock_func.return_value = sentinel_result

            result = visualizer.visualize(payload)

            mock_func.assert_called_once_with(payload)
            self.assertEqual(result, sentinel_result)

    def test_export_stream_simulation(self):
        random_content = f"content_{uuid.uuid4().hex}".encode("utf-8")
        stream_buffer = io.BytesIO(random_content)

        portfolio_id = f"port_{uuid.uuid4().hex}"
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "export_to_text_report": True,
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertEqual(stream_buffer.read(), random_content)


if __name__ == "__main__":
    unittest.main()