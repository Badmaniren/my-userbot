import json
import os
import random
import subprocess
import tempfile
import unittest
import uuid

from skills.anomaly_audit_exporter import (
    AnomalyAuditExporter,
    AnomalyAuditExporterError,
)


class TestAnomalyAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = os.path.join(self.temp_dir.name, "repo_" + uuid.uuid4().hex[:8])
        os.makedirs(self.repo_path, exist_ok=True)

        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "TestRunner"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "runner@test.local"], check=True)

        init_file = os.path.join(self.repo_path, "init_" + uuid.uuid4().hex[:6] + ".txt")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("initial git commit seed " + uuid.uuid4().hex)

        subprocess.run(["git", "-C", self.repo_path, "add", "."], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial test commit"], check=True)

        self.log_path = os.path.join(self.temp_dir.name, "anomalies_" + uuid.uuid4().hex[:8] + ".json")
        self.threshold = round(random.uniform(10.0, 50.0), 2)
        self.exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_log_anomaly_aggregate_and_export_flow(self):
        source = f"sensor_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["low", "medium", "high", "critical"])
        random_id = str(uuid.uuid4())
        random_val = random.randint(1000, 9999)
        details = {
            "entity_id": random_id,
            "metric_score": random_val,
            "description": f"Integration audit trigger {random_id}",
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(5.0, 95.0), 2),
            "memory_mb": random.randint(256, 4096),
            "trace_id": uuid.uuid4().hex,
        }

        self.exporter.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot,
        )

        metric_name = f"latency_p99_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(50.0, 100.0), 2)
        agg_result = self.exporter.aggregate_and_report(metric_name, metric_value)
        self.assertIsInstance(agg_result, dict)

        output_file = os.path.join(self.temp_dir.name, f"export_{uuid.uuid4().hex}.json")
        report = self.exporter.export_report(output_path=output_file)

        self.assertIn("hub_report", report)
        self.assertIn("logger_report", report)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(report, persisted_data)
        persisted_str = json.dumps(persisted_data, ensure_ascii=False)
        self.assertIn(source, persisted_str)
        self.assertIn(random_id, persisted_str)

        anomalies_in_logger = self.exporter.logger.get_anomalies()
        self.assertTrue(any(a.get("source") == source for a in anomalies_in_logger))

    def test_export_report_raises_custom_error_on_invalid_path(self):
        invalid_path = os.path.join(self.temp_dir.name, "non_existent_folder", "sub", "report.json")
        with self.assertRaises(AnomalyAuditExporterError):
            self.exporter.export_report(output_path=invalid_path)

    def test_log_anomaly_raises_custom_error_on_invalid_types(self):
        with self.assertRaises(AnomalyAuditExporterError):
            self.exporter.log_anomaly(
                source=None,
                severity=None,
                details=None,
                telemetry_snapshot="invalid_type_instead_of_dict",
            )


if __name__ == "__main__":
    unittest.main()