import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import sys
import io

from skills.market_portfolio_stress_audit_risk_telemetry import start_new, MarketPortfolioStressAuditRiskTelemetryClass


class TestMarketPortfolioStressAuditRiskTelemetry(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.audit_id = uuid.uuid4().hex
        self.telemetry_id = uuid.uuid4().hex
        self.error_message = f"error_{uuid.uuid4().hex}"

    def test_start_new_success_flow(self):
        rand_stream = uuid.uuid4().hex
        collected_data = {
            "portfolio_id": self.portfolio_id,
            "audit_id": self.audit_id,
            "telemetry_id": self.telemetry_id
        }
        export_data = {
            "exported_field": uuid.uuid4().hex
        }

        mock_collector = MagicMock()
        mock_collector.collect.return_value = collected_data

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = export_data

        dependencies = {
            "market_portfolio_collector_agent": mock_collector,
            "market_portfolio_stress_audit_exporter_v2": mock_exporter
        }

        with patch("skills.market_portfolio_stress_audit_risk_telemetry.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response

            result = start_new(dependencies, telemetry_stream=rand_stream)

            mock_collector.collect.assert_called_once_with(rand_stream)
            mock_exporter.export.assert_called_once_with(collected_data)
            
            self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(result.get("audit_id"), self.audit_id)
            self.assertEqual(result.get("telemetry_id"), self.telemetry_id)
            self.assertEqual(result.get("exported_field"), export_data["exported_field"])
            
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertTrue(called_url.endswith("/telemetry"))

    def test_start_new_collector_exception(self):
        mock_collector = MagicMock()
        mock_collector.collect.side_effect = Exception(self.error_message)

        dependencies = {
            "market_portfolio_collector_agent": mock_collector
        }

        with patch("skills.market_portfolio_stress_audit_risk_telemetry.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as ctx:
                start_new(dependencies)

            self.assertIn(self.error_message, str(ctx.exception))
            mock_post.assert_called_once()
            called_json = mock_post.call_args[1].get("json")
            self.assertEqual(called_json.get("error"), self.error_message)
            mock_response.raise_for_status.assert_called_once()

    def test_market_portfolio_stress_audit_risk_telemetry_class(self):
        instance = MarketPortfolioStressAuditRiskTelemetryClass()
        input_data = {
            "portfolio_id": self.portfolio_id,
            "audit_id": self.audit_id
        }

        output = instance.process_telemetry(input_data)

        self.assertEqual(output.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(output.get("audit_id"), self.audit_id)
        self.assertIn("telemetry_id", output)
        self.assertEqual(output.get("status"), "processed")


if __name__ == "__main__":
    unittest.main()