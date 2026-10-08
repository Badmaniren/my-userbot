import io
import json
import os
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import requests

from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main,
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
            market_report_generator=self.market_report_generator,
        )

    def test_export_report_success(self):
        audit_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        export_format = ''.join(random.choices(string.ascii_lowercase, k=5))
        destination_path = f"/tmp/{''.join(random.choices(string.ascii_lowercase, k=8))}.bin"
        report_content = ''.join(random.choices(string.ascii_letters, k=30)).encode('utf-8')

        audit_data_mock = {"audit_id": audit_id}
        self.db_storage.fetch_audit.return_value = audit_data_mock
        self.market_portfolio_stress_reporter.generate_report.return_value = report_content

        with patch("os.path.exists", return_value=True), patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = self.exporter.export_report(audit_id, export_format, destination_path)

        self.assertTrue(result)
        self.db_storage.fetch_audit.assert_called_once_with(audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_called_once_with(audit_data_mock, export_format)
        mock_file.assert_called_once_with(destination_path, "wb")
        mock_file().write.assert_called_once_with(report_content)

    def test_export_report_audit_not_found(self):
        audit_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        export_format = ''.join(random.choices(string.ascii_lowercase, k=5))
        destination_path = f"/tmp/{''.join(random.choices(string.ascii_lowercase, k=8))}.bin"

        self.db_storage.fetch_audit.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.exporter.export_report(audit_id, export_format, destination_path)

        self.assertIn(audit_id, str(ctx.exception))
        self.db_storage.fetch_audit.assert_called_once_with(audit_id)
        self.market_portfolio_stress_reporter.generate_report.assert_not_called()

    def test_stream_audit_summary(self):
        audit_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_bytes = bytes(random.choices(range(256), k=32))
        expected_stream = io.BytesIO(random_bytes)

        self.market_portfolio_stress_audit_summary_vault.load_summary.return_value = expected_stream

        result_stream = self.exporter.stream_audit_summary(audit_id)

        self.assertIsInstance(result_stream, io.BytesIO)
        self.assertEqual(result_stream.read(), random_bytes)
        self.market_portfolio_stress_audit_summary_vault.load_summary.assert_called_once_with(audit_id)

    def test_process_and_dispatch_anomaly_audit_success(self):
        audit_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        webhook_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=8))}.com/webhook"
        extracted_payload = {"data_key": ''.join(random.choices(string.ascii_lowercase, k=6))}
        evaluation_result = {"status": "anomaly", "score": random.random()}

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
        audit_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        webhook_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=8))}.com/webhook"
        extracted_payload = {"data_key": ''.join(random.choices(string.ascii_lowercase, k=6))}
        evaluation_result = {"status": "normal"}

        self.extractor_tool_1.extract.return_value = extracted_payload
        self.market_anomaly_detector.evaluate.return_value = evaluation_result

        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 403, 500, 502])

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = self.exporter.process_and_dispatch_anomaly_audit(audit_id, webhook_url)

        self.assertFalse(result)
        mock_post.assert_called_once_with(webhook_url, json=evaluation_result)

    def test_market_portfolio_stress_audit_exporter_v2_main(self):
        run_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        portfolio_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        stress_factor = round(random.uniform(0.1, 10.0), 2)

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        expected_export_path = f"/tmp/{run_id}.json"

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["export_path"], expected_export_path)

        mock_file.assert_called_once_with(expected_export_path, "w", encoding="utf-8")
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        dumped_data = args[0]
        self.assertEqual(dumped_data["run_id"], run_id)
        self.assertEqual(dumped_data["portfolio_id"], portfolio_id)
        self.assertEqual(dumped_data["stress_factor"], stress_factor)
        self.assertEqual(dumped_data["status"], "success")


if __name__ == "__main__":
    unittest.main()