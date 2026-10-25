import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.anomaly_verifier import AnomalyVerifier, AnomalyVerifierError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector


class TestIntegrationAnomalyVerifier(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        subprocess_init = subprocess.run(["git", "init"], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(subprocess_init.returncode, 0, "Failed to init git repo for integration test")

        subprocess.run(["git", "config", "user.name", "Architect Test"], cwd=self.repo_path)
        subprocess.run(["git", "config", "user.email", "architect@test.com"], cwd=self.repo_path)

        self.target_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)

        self.initial_content = f"Initial metric value: {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        subprocess.run(["git", "add", self.target_filename], cwd=self.repo_path)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.repo_path)

    def test_integration_verify_patch_and_audit_hub(self):
        patch_id = f"patch-{uuid.uuid4()}"
        log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex[:6]}.log")
        threshold = float(random.randint(5, 50))

        audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=log_path, threshold=threshold)
        verifier = AnomalyVerifier(repo_path=self.repo_path)
        git_inspector = GitInspector(repo_path=self.repo_path)

        new_content = f"Updated metric value: {random.randint(101, 200)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        verification_result = verifier.verify_patch(patch_id=patch_id, target_file=self.target_filename)
        self.assertTrue(verification_result)

        history = git_inspector.get_history()
        self.assertIsNotNone(history)

        autofix_success = verifier.run_autofix_verification(patch_id=patch_id)
        self.assertTrue(autofix_success)

        severity = "HIGH" if random.choice([True, False]) else "MEDIUM"
        details = f"Verified patch {patch_id} successfully on file {self.target_filename}"
        telemetry_snapshot = {"metric": random.uniform(10.0, 99.9)}

        audit_hub.log_anomaly(
            source="anomaly_verifier",
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        metric_name = "test_metric"
        metric_value = float(random.randint(1, 100))
        aggregate_res = audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        self.assertIsNotNone(aggregate_res)

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)
        self.assertTrue(os.path.exists(log_path))


if __name__ == '__main__':
    unittest.main()
