import unittest
import uuid
import random
import os
import tempfile
from skills.audit_pipeline_bridge import AuditPipelineBridge
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_pipeline import AnomalyPipeline


class TestAuditPipelineBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.bridge = AuditPipelineBridge(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_composition_and_real_pipeline_execution(self):
        self.assertIsInstance(self.bridge.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(self.bridge.pipeline, AnomalyPipeline)

        execution_id = f"exec-{uuid.uuid4()}"
        random_metric = f"metric-{uuid.uuid4()}"
        random_value = round(random.uniform(10.0, 500.0), 2)

        payload = {
            "source": f"source-{uuid.uuid4()}",
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "details": f"Test security anomaly details {uuid.uuid4()}",
            "telemetry_snapshot": {
                "cpu_load": round(random.uniform(0.0, 100.0), 2),
                "memory_usage": round(random.uniform(0.0, 100.0), 2)
            }
        }

        result = self.bridge.run_security_audit_pipeline(
            execution_id=execution_id,
            metrics_payload={random_metric: random_value},
            raw_input_data=payload
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл должен быть создан в процессе работы конвейера")

        with open(self.log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(payload["source"], log_content)
            self.assertIn(payload["details"], log_content)

        final_report = self.bridge.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)


if __name__ == "__main__":
    unittest.main()