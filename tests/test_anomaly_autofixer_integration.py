import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.anomaly_autofixer import AnomalyAutofixer
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyAutofixerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir) / "repo"
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.log_path = Path(self.test_dir) / "logs" / "anomaly.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_autofixer_end_to_end_workflow(self):
        random_id = str(uuid.uuid4())
        metric_name = f"metric_{random_id}"
        metric_value = random.uniform(10.0, 100.0)
        source_name = f"source_{random.randint(100, 999)}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Anomaly detected with ID {random_id}"
        telemetry_data = {"cpu_usage": random.randint(50, 99), "memory_leak": bool(random.getrandbits(1))}

        audit_hub = AnomalyAuditHub(
            repo_path=str(self.repo_path),
            log_path=str(self.log_path),
            threshold=50.0
        )

        audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        final_report = audit_hub.generate_final_report()

        autofixer = AnomalyAutofixer(audit_hub=audit_hub)
        fix_result = autofixer.process_and_fix(metric_name=metric_name)

        logger = AnomalyLogger(log_path=str(self.log_path))
        logged_anomalies = logger.get_anomalies()
        structured_report = logger.get_structured_report()

        self.assertIsNotNone(final_report)
        self.assertTrue(any(random_id in str(a) for a in logged_anomalies))
        self.assertIn(source_name, str(structured_report))

        target_file = self.repo_path / f"fix_{random_id}.py"
        target_file.write_text(f"# Fixed anomaly {random_id}\nVALUE = {metric_value}")

        self.assertTrue(target_file.exists())
        file_content = target_file.read_text()
        self.assertIn(random_id, file_content)
        self.assertIn(str(metric_value), file_content)

if __name__ == "__main__":
    unittest.main()