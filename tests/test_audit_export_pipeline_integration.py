import unittest
import os
import tempfile
import uuid
import random
from skills.audit_export_pipeline import AuditExportPipeline


class TestAuditExportPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4().hex}.log")
        self.output_json_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4().hex}.json")
        self.stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        self.stream_output_path = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4().hex}.json")

        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_audit_and_export_integration(self):
        source = f"service_{uuid.uuid4().hex[:6]}"
        severities = ["INFO", "WARNING", "CRITICAL", "ERROR"]
        severity = random.choice(severities)
        details = f"Integration test anomaly details: {uuid.uuid4().hex}"

        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": random.randint(1024, 8192),
            "random_seed": random.randint(1, 1000)
        }

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        self.pipeline.run_audit_and_export(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot,
            metric_name=metric_name,
            metric_value=metric_value,
            output_json_path=self.output_json_path
        )

        self.assertTrue(
            os.path.exists(self.output_json_path),
            f"Expected export file to be created at {self.output_json_path}"
        )

        file_size = os.path.getsize(self.output_json_path)
        self.assertGreater(
            file_size, 0,
            f"Exported JSON report at {self.output_json_path} should not be empty"
        )

    def test_export_stream_integration(self):
        result_path = self.pipeline.export_stream(
            stream_id=self.stream_id,
            output_path=self.stream_output_path
        )

        self.assertEqual(
            result_path, self.stream_output_path,
            "export_stream should return the provided output path"
        )
        self.assertTrue(
            os.path.exists(self.stream_output_path),
            f"Expected stream export file to be created at {self.stream_output_path}"
        )

        file_size = os.path.getsize(self.stream_output_path)
        self.assertGreater(
            file_size, 0,
            f"Exported stream file at {self.stream_output_path} should not be empty"
        )


if __name__ == "__main__":
    unittest.main()