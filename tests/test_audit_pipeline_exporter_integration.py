import unittest
import os
import tempfile
import uuid
import random

from skills.anomaly_pipeline import AnomalyPipeline
from skills.digest_exporter import DigestExporter
from skills.stability_digest import StabilityDigest
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_correlator import AnomalyCorrelator
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.audit_pipeline_exporter import AuditPipelineExporter


class TestAuditPipelineExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        self.execution_id = str(uuid.uuid4())
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.uniform(10.0, 100.0)

        self.raw_input_data = {
            "id": self.execution_id,
            "metric": self.metric_name,
            "value": self.metric_value,
            "source": f"source_{random.randint(1, 100)}",
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "details": f"Execution details for {self.execution_id}",
            "telemetry_snapshot": {self.metric_name: self.metric_value}
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_pipeline_and_export_integration(self):
        threshold = random.uniform(50.0, 150.0)

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=threshold)
        pipeline_result = pipeline.run(self.raw_input_data)

        self.assertIsNotNone(pipeline_result, "AnomalyPipeline must return a valid processing result")

        log_path = os.path.join(self.repo_path, "anomalies.log")
        anomaly_detector = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=log_path,
            threshold=threshold
        )
        system_telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            anomaly_detector=anomaly_detector
        )
        stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=anomaly_detector,
            system_telemetry=system_telemetry
        )
        anomaly_visualizer = AnomalyVisualizer()

        exporter = DigestExporter(stability_digest=stability_digest, anomaly_visualizer=anomaly_visualizer)

        audit_exporter = AuditPipelineExporter(pipeline=pipeline, exporter=exporter)

        output_json_filename = f"report_{uuid.uuid4()}.json"
        output_json_path = os.path.join(self.repo_path, output_json_filename)

        exported_path = audit_exporter.generate_and_export_audit_report(
            raw_data=self.raw_input_data,
            output_path=output_json_path
        )

        self.assertTrue(os.path.exists(exported_path), "Integration must successfully generate and save the report file on disk")

        with open(exported_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Exported report file must not be empty")
            self.assertIn(self.execution_id, content, "Exported report must contain dynamically generated execution ID")

if __name__ == "__main__":
    unittest.main()