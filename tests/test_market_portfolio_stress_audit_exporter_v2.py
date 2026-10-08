import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2
)

class TestMarketPortfolioStressAuditExporterV2(unittest.TestCase):

    def setUp(self):
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

    def test_export_stress_audit_report_success(self):
        random_audit_id = uuid.uuid4().hex
        random_format = random.choice(["json", "csv", "pdf", "xml"])
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        
        self.db_storage.fetch_audit.return_value = {
            "audit_id": random_audit_id,
            "status": "completed",
            "score": random.uniform(1.0, 100.0)
        }
        
        self.market_portfolio_stress_reporter.generate_report.return_value = random_content

        mock_file_path = f"/tmp/{uuid.uuid4().hex}.{random_format}"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            result = self.exporter.export_report(
                audit_id=random_audit_id,
                export_format=random_format,
                destination_path=mock_file_path
            )

            self.assertTrue(result)
            self.db_storage.fetch_audit.assert_called_once_with(random_audit_id)
            self.market_portfolio_stress_reporter.generate_report.assert_called_once()
            mock_file.assert_called_once_with(mock_file_path, "wb")
            mock_file().write.assert_called_once_with(random_content)

    def test_export_stress_audit_report_not_found(self):
        random_audit_id = uuid.uuid4().hex
        random_format = random.choice(["json", "csv", "pdf"])
        random_destination = f"/var/reports/{uuid.uuid4().hex}"

        self.db_storage.fetch_audit.return_value = None

        with self.assertRaises(ValueError):
            self.exporter.export_report(
                audit_id=random_audit_id,
                export_format=random_format,
                destination_path=random_destination
            )

        self.db_storage.fetch_audit.assert_called_once_with(random_audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_not_called()

    def test_stream_stress_audit_bytes_io(self):
        random_audit_id = uuid.uuid4().hex
        random_bytes_data = uuid.uuid4().bytes + uuid.uuid4().bytes
        
        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = io.BytesIO(random_bytes_data)

        stream_result = self.exporter.stream_audit_summary(audit_id=random_audit_id)

        self.assertIsInstance(stream_result, io.BytesIO)
        self.assertEqual(stream_result.getvalue(), random_bytes_data)
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(random_audit_id)

    def test_extract_and_export_with_anomaly_detection(self):
        random_audit_id = uuid.uuid4().hex
        random_anomaly_score = random.randint(500, 9999)
        random_payload = {
            "id": random_audit_id,
            "metric": random_anomaly_score
        }

        self.extractor_tool_1.extract.return_value = random_payload
        self.market_anomaly_detector.evaluate.return_value = {"risk_level": "CRITICAL", "score": random_anomaly_score}

        random_webhook_url = f"https://{uuid.uuid4().hex}.internal/hook"
        with patch("skills.market_portfolio_stress_audit_exporter_v2.requests") as mock_requests:
            if mock_requests is not None:
                mock_requests.post.return_value.status_code = 200

            status = self.exporter.process_and_dispatch_anomaly_audit(
                audit_id=random_audit_id,
                webhook_url=random_webhook_url
            )

            self.assertTrue(status)
            self.extractor_tool_1.extract.assert_called_once_with(random_audit_id)
            self.market_anomaly_detector.evaluate.assert_called_once_with(random_payload)