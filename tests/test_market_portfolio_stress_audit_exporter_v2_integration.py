import unittest
import os
import uuid
import json
import io
import tempfile
from unittest.mock import MagicMock, patch

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_summary_vault_main,
    market_portfolio_stress_audit_exporter_v2_main
)


class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def setUp(self):
        self.audit_id = str(uuid.uuid4())
        self.portfolio_id = str(uuid.uuid4())
        self.stress_factor = round(float(uuid.uuid4().int % 100) / 10.0, 2)
        self.export_format = "json"
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.destination_path = os.path.join(self.temp_dir.name, f"{self.audit_id}.{self.export_format}")

        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        self.market_portfolio_stress_audit_summary_vault = MagicMock()
        self.market_report_generator = MagicMock()

        self.exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2,
            market_anomaly_detector=self.market_anomaly_detector,
            market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
            market_portfolio_stress_audit_summary_vault=self.market_portfolio_stress_audit_summary_vault,
            market_report_generator=self.market_report_generator
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_report_integration(self):
        expected_content = json.dumps({
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_factor": self.stress_factor
        }).encode("utf-8")

        audit_record = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "data": "valid_stress_data"
        }

        self.db_storage.fetch_audit.return_value = audit_record
        self.market_portfolio_stress_reporter.generate_report.return_value = expected_content

        result = self.exporter.export_report(
            audit_id=self.audit_id,
            export_format=self.export_format,
            destination_path=self.destination_path
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.destination_path))
        
        with open(self.destination_path, "rb") as f:
            written_content = f.read()
        
        self.assertEqual(written_content, expected_content)
        self.db_storage.fetch_audit.assert_called_once_with(self.audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_called_once_with(audit_record, self.export_format)

    def test_export_report_not_found(self):
        self.db_storage.fetch_audit.return_value = None

        with self.assertRaises(ValueError) as context:
            self.exporter.export_report(
                audit_id=self.audit_id,
                export_format=self.export_format,
                destination_path=self.destination_path
            )

        self.assertIn(self.audit_id, str(context.exception))
        self.assertFalse(os.path.exists(self.destination_path))

    def test_stream_audit_summary_integration(self):
        stream_data = io.BytesIO(b"random_stream_content_" + uuid.uuid4().bytes)
        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = stream_data

        result_stream = self.exporter.stream_audit_summary(self.audit_id)

        self.assertEqual(result_stream, stream_data)
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(self.audit_id)

    @patch("skills.market_portfolio_stress_audit_exporter_v2.requests.post")
    def test_process_and_dispatch_anomaly_audit_integration(self, mock_requests_post):
        webhook_url = f"https://example.webhook.internal/api/v1/audit/{uuid.uuid4()}"
        extracted_payload = {"audit_id": self.audit_id, "metrics": uuid.uuid4().int}
        evaluation_result = {"status": "anomaly_detected", "severity": "HIGH"}

        self.extractor_tool_1.extract.return_value = extracted_payload
        self.market_anomaly_detector.evaluate.return_value = evaluation_result

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        success = self.exporter.process_and_dispatch_anomaly_audit(self.audit_id, webhook_url)

        self.assertTrue(success)
        self.extractor_tool_1.extract.assert_called_once_with(self.audit_id)
        self.market_anomaly_detector.evaluate.assert_called_once_with(extracted_payload)
        mock_requests_post.assert_called_once_with(webhook_url, json=evaluation_result)

    def test_vault_and_main_runners_integration(self):
        run_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        stress_factor = float(uuid.uuid4().int % 1000) / 100.0

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        vault_result = market_portfolio_stress_audit_summary_vault_main(payload)

        self.assertEqual(vault_result["status"], "success")
        self.assertEqual(vault_result["run_id"], run_id)
        self.assertEqual(vault_result["portfolio_id"], portfolio_id)
        
        expected_file_path = vault_result["export_path"]
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["run_id"], run_id)
        self.assertEqual(file_data["portfolio_id"], portfolio_id)
        self.assertEqual(file_data["stress_factor"], stress_factor)
        self.assertEqual(file_data["status"], "success")

        main_result = market_portfolio_stress_audit_exporter_v2_main(payload)
        self.assertEqual(main_result, vault_result)

        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)


if __name__ == "__main__":
    unittest.main()