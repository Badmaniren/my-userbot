import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_exporter import AnomalyAuditExporter
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter

class TestAnomalyAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.output_json_path = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.json")
        self.output_html_path = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.html")

        self.threshold = random.uniform(0.5, 0.99)
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.uniform(10.0, 100.0)

        self.source = f"source_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.details = f"test_details_{uuid.uuid4().hex}"
        self.telemetry_snapshot = {"cpu": random.randint(1, 100), "memory": random.randint(100, 1000)}

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_audit_and_export_composition(self):
        exporter_instance = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.assertIsInstance(exporter_instance.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(exporter_instance.digest_exporter, DigestExporter)

        exporter_instance.audit_hub.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry_snapshot
        )

        agg_result = exporter_instance.audit_hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = exporter_instance.audit_hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, list, str))

        json_result = exporter_instance.export_json_report(self.output_json_path)
        self.assertTrue(os.path.exists(self.output_json_path))
        self.assertGreater(os.path.getsize(self.output_json_path), 0)
        self.assertEqual(json_result, self.output_json_path)

        html_result = exporter_instance.export_html_report(self.output_html_path)
        self.assertTrue(os.path.exists(self.output_html_path))
        self.assertGreater(os.path.getsize(self.output_html_path), 0)
        self.assertEqual(html_result, self.output_html_path)

if __name__ == "__main__":
    unittest.main()