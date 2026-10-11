import os
import uuid
import json
import io
import unittest
from unittest.mock import patch, MagicMock

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def setUp(self):
        self.audit_id = str(uuid.uuid4())
        self.portfolio_id = str(uuid.uuid4())
        self.stress_factor = float(uuid.uuid4().int % 100) / 10.0
        self.destination_path = f"/tmp/audit_report_{uuid.uuid4()}.bin"
        self.webhook_url = "https://httpbin.org/post"

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
        if os.path.exists(self.destination_path):
            try:
                os.remove(self.destination_path)
            except OSError:
                pass
        
        tmp_summary_path = f"/tmp/{self.audit_id}.json"
        if os.path.exists(tmp_summary_path):
            try:
                os.remove(tmp_summary_path)
            except OSError:
                pass

    def test_export_report_integration(self):
        expected_content = f"audit_content_{uuid.uuid4()}".encode("utf-8")
        export_format = "pdf"

        self.db_storage.fetch_audit.return_value = {"audit_id": self.audit_id, "data": "test"}
        self.market_portfolio_stress_reporter.generate_report.return_value = expected_content

        result = self.exporter.export_report(self.audit_id, export_format, self.destination_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.destination_path))
        
        with open(self.destination_path, "rb") as f:
            content = f.read()
        self.assertEqual(content, expected_content)
        self.db_storage.fetch_audit.assert_called_once_with(self.audit_id)

    def test_stream_audit_summary_integration(self):
        expected_stream = io.BytesIO(f"summary_{uuid.uuid4()}".encode("utf-8"))
        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = expected_stream

        stream = self.exporter.stream_audit_summary(self.audit_id)

        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.getvalue(), expected_stream.getvalue())
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(self.audit_id)

    @patch('requests.post')
    def test_process_and_dispatch_anomaly_audit_integration(self, mock_post):
        payload_data = {"anomaly_score": float(uuid.uuid4().int % 100)}
        evaluation_data = {"status": "anomaly_detected", "run_id": self.audit_id}

        self.extractor_tool_1.extract.return_value = payload_data
        self.market_anomaly_detector.evaluate.return_value = evaluation_data
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        success = self.exporter.process_and_dispatch_anomaly_audit(self.audit_id, self.webhook_url)

        self.assertTrue(success)
        self.extractor_tool_1.extract.assert_called_once_with(self.audit_id)
        self.market_anomaly_detector.evaluate.assert_called_once_with(payload_data)
        mock_post.assert_called_once_with(self.webhook_url, json=evaluation_data)

    def test_main_function_integration(self):
        payload = {
            "run_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_factor": self.stress_factor
        }

        result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], self.audit_id)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        
        expected_path = result["export_path"]
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["run_id"], self.audit_id)
        self.assertEqual(data["portfolio_id"], self.portfolio_id)
        self.assertEqual(data["stress_factor"], self.stress_factor)
        self.assertEqual(data["status"], "success")

        if os.path.exists(expected_path):
            os.remove(expected_path)


if __name__ == "__main__":
    unittest.main()