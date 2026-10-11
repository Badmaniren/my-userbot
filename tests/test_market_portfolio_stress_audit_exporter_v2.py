import io
import json
import os
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_summary_vault_main,
    market_portfolio_stress_audit_exporter_v2_main
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

    def test_export_report_success(self):
        audit_id = uuid.uuid4().hex
        export_format = random.choice(["pdf", "csv", "json", "xml"])
        destination_path = f"/tmp/{uuid.uuid4().hex}.{export_format}"
        
        expected_audit_data = {"audit_id": audit_id, "status": "verified"}
        expected_content = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")

        self.db_storage.fetch_audit.return_value = expected_audit_data
        self.market_portfolio_stress_reporter.generate_report.return_value = expected_content

        with patch("os.path.exists", return_value=True) as mock_exists:
            result = self.exporter.export_report(audit_id, export_format, destination_path)

        self.assertTrue(result)
        self.db_storage.fetch_audit.assert_called_once_with(audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_called_once_with(expected_audit_data, export_format)
        mock_exists.assert_called_once_with(destination_path)

    def test_export_report_not_found(self):
        audit_id = uuid.uuid4().hex
        export_format = random.choice(["pdf", "csv", "json"])
        destination_path = f"/tmp/{uuid.uuid4().hex}"

        self.db_storage.fetch_audit.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.exporter.export_report(audit_id, export_format, destination_path)

        self.assertIn(audit_id, str(ctx.exception))
        self.db_storage.fetch_audit.assert_called_once_with(audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_not_called()

    def test_stream_audit_summary(self):
        audit_id = uuid.uuid4().hex
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)

        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = stream_mock

        result = self.exporter.stream_audit_summary(audit_id)

        self.assertIsInstance(result, io.BytesIO)
        self.assertEqual(result.read(), random_bytes)
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(audit_id)

    def test_process_and_dispatch_anomaly_audit_success(self):
        audit_id = uuid.uuid4().hex
        webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        
        extracted_payload = {"risk_score": random.uniform(1.0, 100.0)}
        evaluation_result = {"anomaly_detected": random.choice([True, False]), "code": random.randint(100, 999)}

        self.extractor_tool_1.extract.return_value = extracted_payload
        self.market_anomaly_detector.evaluate.return_value = evaluation_result

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = self.exporter.process_and_dispatch_anomaly_audit(audit_id, webhook_url)

        self.assertTrue(result)
        self.extractor_tool_1.extract.assert_called_once_with(audit_id)
        self.market_anomaly_detector.evaluate.assert_called_once_with(extracted_payload)
        mock_post.assert_called_once_with(webhook_url, json=evaluation_result)

    def test_process_and_dispatch_anomaly_audit_failure(self):
        audit_id = uuid.uuid4().hex
        webhook_url = f"https://{uuid.uuid4().hex}.net/hook"
        
        extracted_payload = {"metric": uuid.uuid4().hex}
        evaluation_result = {"status": "rejected"}

        self.extractor_tool_1.extract.return_value = extracted_payload
        self.market_anomaly_detector.evaluate.return_value = evaluation_result

        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 404, 500, 502])

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = self.exporter.process_and_dispatch_anomaly_audit(audit_id, webhook_url)

        self.assertFalse(result)
        mock_post.assert_called_once_with(webhook_url, json=evaluation_result)

    def test_market_portfolio_stress_audit_summary_vault_main(self):
        run_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        stress_factor = random.uniform(0.0, 1.0)

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = market_portfolio_stress_audit_summary_vault_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["export_path"], f"/tmp/{run_id}.json")
        mock_file.assert_called_once_with(f"/tmp/{run_id}.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    def test_market_portfolio_stress_audit_exporter_v2_main(self):
        run_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        stress_factor = random.uniform(1.0, 10.0)

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()):
            with patch("json.dump"):
                result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["export_path"], f"/tmp/{run_id}.json")