import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_bridge import AnomalyAuditBridge
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter
from skills.stability_digest import StabilityDigest

class TestAnomalyAuditBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.log")
        self.json_output = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.json")
        self.html_output = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.html")

        self.repo_path = self.test_dir.name
        self.threshold = random.uniform(0.5, 0.9)

        self.bridge = AnomalyAuditBridge(
            repo_path_or_hub=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_audit_and_export_pipeline(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Test anomaly event {uuid.uuid4().hex}"
        telemetry_data = {"cpu_load": random.randint(10, 100), "memory_usage": random.random()}

        log_res = self.bridge.log_anomaly(source_id, severity_level, details_msg, telemetry_data)
        self.assertIsNotNone(log_res)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(1.0, 100.0)
        agg_res = self.bridge.aggregate_and_report(metric_name, metric_value)
        self.assertIsNotNone(agg_res)

        final_report = self.bridge.generate_final_report()
        self.assertIsInstance(final_report, dict)

        export_json_res = self.bridge.process_and_export(self.json_output)
        self.assertTrue(os.path.exists(self.json_output))
        self.assertGreater(os.path.getsize(self.json_output), 0)

        html_res = self.bridge.export_html_report(self.html_output)
        self.assertTrue(os.path.exists(self.html_output))
        self.assertGreater(os.path.getsize(self.html_output), 0)

    def test_bridge_with_preconstructed_hub(self):
        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_file, threshold=self.threshold)
        stability_inst = StabilityDigest()
        exporter = DigestExporter(stability_digest=stability_inst)

        custom_bridge = AnomalyAuditBridge(audit_hub=hub, digest_exporter=exporter)

        source_id = f"custom_src_{uuid.uuid4().hex[:6]}"
        custom_bridge.log_anomaly(source_id, "LOW", "Custom integration test", {"ping": uuid.uuid4().hex})

        report_path = os.path.join(self.test_dir.name, f"custom_export_{uuid.uuid4().hex}.json")
        custom_bridge.process_and_export(report_path)

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(source_id, content)

if __name__ == "__main__":
    unittest.main()