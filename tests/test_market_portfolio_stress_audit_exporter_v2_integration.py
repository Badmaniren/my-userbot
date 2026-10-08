import unittest
import uuid
import random
import os
import io
import json
from unittest.mock import patch, MagicMock

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def setUp(self):
        self.audit_id = str(uuid.uuid4())
        self.portfolio_id = str(uuid.uuid4())
        self.stress_factor = round(random.uniform(1.0, 10.0), 2)
        self.destination_path = f"/tmp/test_audit_report_{uuid.uuid4()}.bin"
        
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
            os.remove(self.destination_path)
        tmp_json = f"/tmp/{self.audit_id}.json"
        if os.path.exists(tmp_json):
            os.remove(tmp_json)

    def test_export_report_integration(self):
        expected_content = f"audit_data_content_{uuid.uuid4()}".encode("utf-8")
        self.db_storage.fetch_audit.return_value = {"id": self.audit_id, "status": "active"}
        self.market_portfolio_stress_reporter.generate_report.return_value = expected_content

        result = self.exporter.export_report(self.audit_id, "bin", self.destination_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.destination_path))
        with open(self.destination_path, "rb") as f:
            self.assertEqual(f.read(), expected_content)
        
        self.db_storage.fetch_audit.assert_called_once_with(self.audit_id)

    def test_stream_audit_summary_integration(self):
        expected_stream = io.BytesIO(b"summary_bytes")
        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = expected_stream

        stream = self.exporter.stream_audit_summary(self.audit_id)

        self.assertEqual(stream, expected_stream)
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(self.audit_id)

    @patch('skills.market_portfolio_stress_audit_exporter_v2.requests.post')
    def test_process_and_dispatch_anomaly_audit_integration(self, mock_post):
        webhook_url = f"https://example.com/webhook/{uuid.uuid4()}"
        extracted_payload = {"metric": random.randint(1, 100)}
        evaluation_result = {"anomaly_detected": True, "score": random.random()}

        self.extractor_tool_1.extract.return_value = extracted_payload
        self.market_anomaly_detector.evaluate.return_value = evaluation_result

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        success = self.exporter.process_and_dispatch_anomaly_audit(self.audit_id, webhook_url)

        self.assertTrue(success)
        self.extractor_tool_1.extract.assert_called_once_with(self.audit_id)
        self.market_anomaly_detector.evaluate.assert_called_once_with(extracted_payload)
        mock_post.assert_called_once_with(webhook_url, json=evaluation_result)

    def test_market_portfolio_stress_audit_exporter_v2_main_integration(self):
        payload = {
            "run_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "stress_factor": self.stress_factor
        }

        result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], self.audit_id)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        
        export_path = result["export_path"]
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["run_id"], self.audit_id)
            self.assertEqual(data["portfolio_id"], self.portfolio_id)
            self.assertEqual(data["stress_factor"], self.stress_factor)
            self.assertEqual(data["status"], "success")


if __name__ == "__main__":
    unittest.main()