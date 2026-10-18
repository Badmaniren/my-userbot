import unittest
import os
import json
import uuid
import random
from skills.audit_export_engine import AuditExportEngine
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAuditExportEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_audit_env_{uuid.uuid4().hex}"
        self.log_path = os.path.join(self.test_dir, "anomalies.json")
        self.export_path = os.path.join(self.test_dir, "exports", "final_audit_report.json")

        os.makedirs(self.test_dir, exist_ok=True)

        self.engine = AuditExportEngine(
            repo_path=self.test_dir,
            log_path=self.log_path,
            threshold=random.randint(5, 15)
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)

    def test_log_and_export_anomaly_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Details for anomaly {uuid.uuid4().hex}"
        telemetry_data = {"cpu_load": random.random(), "memory_usage": random.randint(100, 1000)}

        report = self.engine.log_and_export_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        self.assertIsInstance(report, dict)

        streamed_data = self.engine.stream_export_data()
        self.assertTrue(len(streamed_data) > 0)

        matched = False
        for entry in streamed_data:
            if isinstance(entry, dict) and entry.get("source") == source_name:
                self.assertEqual(entry.get("severity"), severity_level)
                self.assertEqual(entry.get("details"), details_msg)
                matched = True
        self.assertTrue(matched, "Logged anomaly was not found in the anomaly stream.")

    def test_aggregate_metric_and_export_integration(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(50, 500)

        aggregated_result = self.engine.aggregate_metric_and_export(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregated_result)

    def test_export_audit_report_file_creation(self):
        source_name = f"source_file_{uuid.uuid4().hex[:8]}"
        severity_level = "HIGH"
        details_msg = f"File export test {uuid.uuid4().hex}"
        telemetry_data = {"disk_io": random.randint(1, 50)}

        self.engine.log_and_export_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        returned_path = self.engine.export_audit_report(self.export_path)

        self.assertEqual(returned_path, self.export_path)
        self.assertTrue(os.path.exists(self.export_path), "Export file was not physically created.")

        with open(self.export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("structured_logs", data)
        self.assertIn("final_report", data)

        logs = data["structured_logs"]
        self.assertTrue(any(isinstance(l, dict) and l.get("source") == source_name for l in logs))

    def test_clear_audit_history_integration(self):
        self.engine.log_and_export_anomaly(
            source=f"src_{uuid.uuid4().hex[:4]}",
            severity="LOW",
            details="to be cleared",
            telemetry_snapshot={"test": 0}
        )

        before_clear = self.engine.stream_export_data()
        self.assertGreater(len(before_clear), 0)

        self.engine.clear_audit_history()

        after_clear = self.engine.stream_export_data()
        self.assertEqual(len(after_clear), 0)


if __name__ == "__main__":
    unittest.main()