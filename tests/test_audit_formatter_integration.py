import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.audit_formatter import AuditFormatter


class TestAuditFormatterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="audit_formatter_test_")
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.log")
        self.logger = AnomalyLogger(self.log_path)
        self.formatter = AuditFormatter()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_format_json_with_live_logger_data(self):
        unique_source = f"service_{uuid.uuid4().hex[:8]}"
        unique_detail = f"failure_trace_{uuid.uuid4().hex}"
        unique_metric = f"cpu_{uuid.uuid4().hex[:6]}"
        unique_value = random.randint(1000, 9999)
        severity = "CRITICAL"

        self.logger.log_anomaly(
            source=unique_source,
            severity=severity,
            details=unique_detail,
            telemetry_snapshot={unique_metric: unique_value}
        )

        report = self.logger.get_structured_report()
        formatted_json = self.formatter.format_json(report)

        self.assertIsInstance(formatted_json, str)
        parsed = json.loads(formatted_json)

        raw_json_str = json.dumps(parsed)
        self.assertIn(unique_source, raw_json_str)
        self.assertIn(unique_detail, raw_json_str)
        self.assertIn(unique_metric, raw_json_str)
        self.assertIn(str(unique_value), raw_json_str)
        self.assertIn(severity, raw_json_str)

    def test_format_markdown_with_multiple_anomalies(self):
        entries = []
        for _ in range(3):
            entry = {
                "source": f"module_{uuid.uuid4().hex[:6]}",
                "severity": random.choice(["WARNING", "ERROR", "CRITICAL"]),
                "details": f"issue_{uuid.uuid4().hex[:12]}",
                "snapshot": {f"lat_{uuid.uuid4().hex[:4]}": random.randint(10, 500)}
            }
            entries.append(entry)
            self.logger.log_anomaly(
                source=entry["source"],
                severity=entry["severity"],
                details=entry["details"],
                telemetry_snapshot=entry["snapshot"]
            )

        report = self.logger.get_structured_report()
        markdown_output = self.formatter.format_markdown(report)

        self.assertIsInstance(markdown_output, str)
        for entry in entries:
            self.assertIn(entry["source"], markdown_output)
            self.assertIn(entry["severity"], markdown_output)
            self.assertIn(entry["details"], markdown_output)

    def test_format_summary_plain_text(self):
        unique_source = f"auth_svc_{uuid.uuid4().hex[:6]}"
        unique_detail = f"token_invalid_{uuid.uuid4().hex}"
        severity = "WARNING"

        self.logger.log_anomaly(
            source=unique_source,
            severity=severity,
            details=unique_detail,
            telemetry_snapshot={"attempt": random.randint(1, 10)}
        )

        report = self.logger.get_structured_report()
        summary = self.formatter.format_summary(report)

        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary.strip()), 0)
        self.assertIn(unique_source, summary)
        self.assertIn(severity, summary)

    def test_export_report_to_files(self):
        unique_token = uuid.uuid4().hex
        self.logger.log_anomaly(
            source=f"exporter_svc_{unique_token[:6]}",
            severity="HIGH",
            details=f"export_detail_{unique_token}",
            telemetry_snapshot={"token": unique_token}
        )
        report = self.logger.get_structured_report()

        json_file = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.json")
        md_file = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.md")

        result_json_path = self.formatter.export_report(report, json_file, format_type="json")
        self.assertTrue(os.path.exists(json_file))
        self.assertEqual(os.path.abspath(json_file), os.path.abspath(result_json_path))
        with open(json_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_token, content)
            parsed = json.loads(content)
            self.assertIsInstance(parsed, (dict, list))

        result_md_path = self.formatter.export_report(report, md_file, format_type="markdown")
        self.assertTrue(os.path.exists(md_file))
        self.assertEqual(os.path.abspath(md_file), os.path.abspath(result_md_path))
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_token, content)


if __name__ == "__main__":
    unittest.main()