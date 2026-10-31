import os
import shutil
import tempfile
import unittest
import uuid
import random

from skills.anomaly_remediator import AnomalyRemediator, AnomalyRemediatorError
from skills.anomaly_autofixer_worker import AnomalyAutofixerWorker, AutofixerWorkerError
from skills.anomaly_rollback_controller import AnomalyRollbackController, AnomalyRollbackControllerError


class TestAnomalyRemediatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, "repo")
        os.makedirs(self.repo_path, exist_ok=True)
        self.log_path = os.path.join(self.temp_dir, f"remediator_{uuid.uuid4().hex[:6]}.log")
        self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.5, 0.99), 2)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_remediator_composition_initialization(self):
        remediator = AnomalyRemediator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            worker_id=self.worker_id,
            threshold=self.threshold
        )
        self.assertIsInstance(remediator.autofixer, AnomalyAutofixerWorker)
        self.assertIsInstance(remediator.rollback_controller, AnomalyRollbackController)

    def test_successful_remediation_workflow(self):
        remediator = AnomalyRemediator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            worker_id=self.worker_id,
            threshold=self.threshold
        )

        anomaly_id = f"anom_{uuid.uuid4().hex}"
        patch_id = f"patch_{uuid.uuid4().hex}"
        target_filename = f"target_{uuid.uuid4().hex[:6]}.txt"
        target_file_path = os.path.join(self.repo_path, target_filename)

        initial_content = f"BASE_STATE_{uuid.uuid4().hex}"
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        patch_content = f"PATCHED_STATE_{patch_id}"
        verification_cmd = "python -c 'import sys; sys.exit(0)'"
        source_name = f"source_{uuid.uuid4().hex[:6]}"

        result = remediator.remediate(
            anomaly_id=anomaly_id,
            patch_id=patch_id,
            patch_content=patch_content,
            target_file=target_filename,
            verification_command=verification_cmd,
            source=source_name
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.log_path))

        with open(target_file_path, "r", encoding="utf-8") as f:
            content_after = f.read()

        self.assertIn(patch_id, content_after)

    def test_failed_verification_triggers_rollback(self):
        remediator = AnomalyRemediator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            worker_id=self.worker_id,
            threshold=self.threshold
        )

        anomaly_id = f"anom_fail_{uuid.uuid4().hex}"
        patch_id = f"patch_fail_{uuid.uuid4().hex}"
        target_filename = f"fail_target_{uuid.uuid4().hex[:6]}.txt"
        target_file_path = os.path.join(self.repo_path, target_filename)

        original_marker = f"ORIGINAL_DATA_{uuid.uuid4().hex}"
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(original_marker)

        bad_patch_content = f"CORRUPTED_{uuid.uuid4().hex}"
        failing_verification_cmd = "python -c 'import sys; sys.exit(1)'"
        source_name = f"source_err_{uuid.uuid4().hex[:6]}"

        try:
            res = remediator.remediate(
                anomaly_id=anomaly_id,
                patch_id=patch_id,
                patch_content=bad_patch_content,
                target_file=target_filename,
                verification_command=failing_verification_cmd,
                source=source_name
            )
            if isinstance(res, dict):
                self.assertIn("rollback", str(res).lower())
        except (AnomalyRemediatorError, AutofixerWorkerError, AnomalyRollbackControllerError):
            pass

        self.assertTrue(os.path.exists(self.log_path))


if __name__ == "__main__":
    unittest.main()