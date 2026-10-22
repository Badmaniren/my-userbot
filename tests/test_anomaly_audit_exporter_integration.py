import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_exporter import AnomalyAuditExporter, AnomalyAuditExporterError


class TestAnomalyAuditExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")
        self.json_path = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.json")
        self.html_path = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.html")

        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_full_workflow(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_text = f"Anomaly details uuid: {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.random(), "memory_usage": random.randint(100, 1000)}

        self.exporter.log_external_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        json_result = self.exporter.aggregate_and_export_json(
            metric_name=metric_name,
            value=metric_value,
            json_path=self.json_path
        )

        self.assertTrue(os.path.exists(self.json_path), "Файл JSON отчета не был создан.")
        self.assertIsInstance(json_result, str)

        with open(self.json_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertTrue(len(content) > 0, "Экспортированный JSON файл пуст.")
            self.assertIn(metric_name, content)

        html_result = self.exporter.export_html(self.html_path)

        self.assertTrue(os.path.exists(self.html_path), "Файл HTML отчета не был создан.")
        self.assertIsInstance(html_result, str)

        with open(self.html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            self.assertTrue(len(html_content) > 0, "Экспортированный HTML файл пуст.")

    def test_export_audit_report(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        self.exporter.log_external_anomaly(
            source=source_name,
            severity="HIGH",
            details="Test audit report export",
            telemetry_snapshot={"status": "unstable"}
        )

        audit_path = os.path.join(self.repo_path, f"audit_report_{uuid.uuid4().hex}.json")
        result = self.exporter.export_audit_report(audit_path)

        self.assertTrue(os.path.exists(audit_path), "Аудит отчет не был экспортирован.")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()