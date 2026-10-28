import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.patch_validator import patch_validator
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestPatchValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = str(Path(self.test_dir) / f"anomaly_log_{uuid.uuid4()}.json")

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.uniform(0.1, 0.9)
        )
        self.anomaly_logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_validation_pipeline_integration(self):
        random_id = str(uuid.uuid4())
        source_name = f"source_{random_id}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_value = random.uniform(10.0, 100.0)

        patch_content = f"""
        diff --git a/test_{random_id}.py b/test_{random_id}.py
        new file mode 100644
        index 0000000..e69de29
        --- /dev/null
        +++ b/test_{random_id}.py
        # Test identifier: {random_id}
        print("Validated patch {random_id}")
        """

        telemetry_data = {
            "random_metric": metric_value,
            "session_id": random_id,
            "status": "active"
        }

        self.anomaly_logger.log_anomaly(
            source=source_name,
            severity=severity_level,
            details={"message": f"Testing patch validation for {random_id}"},
            telemetry_snapshot=telemetry_data
        )

        self.audit_hub.aggregate_and_report(
            metric_name=f"metric_{random_id}",
            value=metric_value
        )

        validation_result = patch_validator(patch_content)

        self.assertIsNotNone(validation_result)

        anomalies = self.anomaly_logger.get_anomalies()
        logged_sources = [a.get("source") for a in anomalies]
        self.assertIn(source_name, logged_sources)

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

if __name__ == "__main__":
    unittest.main()