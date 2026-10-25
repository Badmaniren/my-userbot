import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.anomaly_rollback_controller import anomaly_rollback_controller
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector


class TestAnomalyRollbackControllerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "anomaly_audit.log")
        self.repo_path = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rollback_controller_integration_flow(self):
        unique_source = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.randint(1, 10)
        detail_msg = f"Failed autofix execution ID: {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.random(), "memory_leak": bool(random.getrandbits(1))}

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=random.randint(5, 15)
        )
        audit_hub.log_anomaly(
            source=unique_source,
            severity=severity_level,
            details=detail_msg,
            telemetry_snapshot=telemetry_data
        )

        logger = AnomalyLogger(log_path=self.log_file)
        logged_anomalies = logger.get_anomalies()
        self.assertTrue(any(detail_msg in str(a) for a in logged_anomalies))

        git_inspector = GitInspector(repo_path=self.repo_path)
        repo_history = git_inspector.get_history()
        self.assertIsInstance(repo_history, (list, dict, str))

        controller_result = anomaly_rollback_controller(
            repo_path=self.repo_path,
            log_path=self.log_file,
            anomaly_details=detail_msg
        )

        self.assertIsNotNone(controller_result)

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)


if __name__ == "__main__":
    unittest.main()