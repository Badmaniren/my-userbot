import os
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.anomaly_autofixer_worker import AutofixerWorkerError, PatchApplicationError
from skills.anomaly_rollback_controller import AnomalyRollbackControllerError
from skills.anomaly_remediator import AnomalyRemediator, AnomalyRemediatorError


class TestAnomalyRemediator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.log_path = f"/tmp/logs_{uuid.uuid4().hex}.log"
        self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.anomaly_id = f"anom_{uuid.uuid4().hex}"
        self.patch_id = f"patch_{uuid.uuid4().hex}"
        self.patch_content = f"--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.target_file = f"path/to/{uuid.uuid4().hex}.py"
        self.verification_command = f"python -m unittest test_{uuid.uuid4().hex}.py"
        self.source = f"source_{uuid.uuid4().hex[:6]}"

    def test_initialization_creates_dependencies(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path,
                worker_id=self.worker_id,
                threshold=self.threshold
            )

            mock_worker_cls.assert_called_once_with(
                worker_id=self.worker_id,
                repo_path=self.repo_path,
                log_path=self.log_path
            )
            mock_rollback_cls.assert_called_once_with(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )
            self.assertIsNotNone(remediator)

    def test_remediate_successful_flow(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_worker = mock_worker_cls.return_value
            mock_rollback = mock_rollback_cls.return_value

            expected_result_str = f"FIXED_{uuid.uuid4().hex}"
            mock_worker.process_autofix.return_value = expected_result_str

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path,
                worker_id=self.worker_id,
                threshold=self.threshold
            )

            res = remediator.remediate_anomaly(
                anomaly_id=self.anomaly_id,
                patch_id=self.patch_id,
                patch_content=self.patch_content,
                target_file=self.target_file,
                verification_command=self.verification_command,
                source=self.source
            )

            mock_worker.process_autofix.assert_called_once_with(
                self.anomaly_id,
                self.patch_id,
                self.patch_content,
                self.target_file,
                self.verification_command
            )
            mock_rollback.execute_rollback.assert_not_called()
            self.assertEqual(res.get("status"), "success")
            self.assertEqual(res.get("details"), expected_result_str)

    def test_remediate_patch_application_error_triggers_rollback(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_worker = mock_worker_cls.return_value
            mock_rollback = mock_rollback_cls.return_value

            error_msg = f"Patch error {uuid.uuid4().hex}"
            mock_worker.process_autofix.side_effect = PatchApplicationError(error_msg)
            mock_rollback.execute_rollback.return_value = True

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path,
                worker_id=self.worker_id,
                threshold=self.threshold
            )

            res = remediator.remediate_anomaly(
                anomaly_id=self.anomaly_id,
                patch_id=self.patch_id,
                patch_content=self.patch_content,
                target_file=self.target_file,
                verification_command=self.verification_command,
                source=self.source
            )

            mock_rollback.execute_rollback.assert_called_once_with(self.anomaly_id, self.source)
            self.assertEqual(res.get("status"), "rolled_back")
            self.assertTrue(res.get("rollback_success"))
            self.assertIn(error_msg, res.get("error", ""))

    def test_remediate_worker_error_triggers_rollback(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_worker = mock_worker_cls.return_value
            mock_rollback = mock_rollback_cls.return_value

            error_msg = f"Worker crashed {uuid.uuid4().hex}"
            mock_worker.process_autofix.side_effect = AutofixerWorkerError(error_msg)
            mock_rollback.execute_rollback.return_value = True

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path
            )

            res = remediator.remediate_anomaly(
                anomaly_id=self.anomaly_id,
                patch_id=self.patch_id,
                patch_content=self.patch_content,
                target_file=self.target_file,
                verification_command=self.verification_command,
                source=self.source
            )

            mock_rollback.execute_rollback.assert_called_once_with(self.anomaly_id, self.source)
            self.assertEqual(res.get("status"), "rolled_back")

    def test_remediate_verification_failure_step_by_step(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_worker = mock_worker_cls.return_value
            mock_rollback = mock_rollback_cls.return_value

            mock_worker.apply_patch.return_value = True
            mock_worker.verify_fix.return_value = False
            mock_rollback.execute_rollback.return_value = True

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path
            )

            res = remediator.apply_and_verify(
                anomaly_id=self.anomaly_id,
                patch_id=self.patch_id,
                patch_content=self.patch_content,
                target_file=self.target_file,
                verification_command=self.verification_command,
                source=self.source
            )

            mock_worker.apply_patch.assert_called_once_with(self.patch_id, self.patch_content, self.target_file)
            mock_worker.verify_fix.assert_called_once_with(self.anomaly_id, self.verification_command)
            mock_rollback.execute_rollback.assert_called_once_with(self.anomaly_id, self.source)
            self.assertEqual(res.get("status"), "failed_verification_rolled_back")

    def test_remediate_rollback_failure_raises_remediator_error(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_worker = mock_worker_cls.return_value
            mock_rollback = mock_rollback_cls.return_value

            rollback_err_msg = f"Rollback corrupted {uuid.uuid4().hex}"
            mock_worker.process_autofix.side_effect = AutofixerWorkerError("Worker fail")
            mock_rollback.execute_rollback.side_effect = AnomalyRollbackControllerError(rollback_err_msg)

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path
            )

            with self.assertRaises(AnomalyRemediatorError) as ctx:
                remediator.remediate_anomaly(
                    anomaly_id=self.anomaly_id,
                    patch_id=self.patch_id,
                    patch_content=self.patch_content,
                    target_file=self.target_file,
                    verification_command=self.verification_command,
                    source=self.source
                )

            self.assertIn(rollback_err_msg, str(ctx.exception))

    def test_manual_rollback_restoration_flow(self):
        with patch("skills.anomaly_remediator.AnomalyAutofixerWorker") as mock_worker_cls, \
             patch("skills.anomaly_remediator.AnomalyRollbackController") as mock_rollback_cls:

            mock_rollback = mock_rollback_cls.return_value
            mock_rollback.execute_rollback.return_value = True

            epic_summary = {
                "restored_id": self.anomaly_id,
                "timestamp": random.randint(100000, 999999)
            }
            mock_rollback.finalize_epic_restoration.return_value = epic_summary

            remediator = AnomalyRemediator(
                repo_path=self.repo_path,
                log_path=self.log_path
            )

            status = remediator.force_rollback(self.anomaly_id, self.source)

            mock_rollback.execute_rollback.assert_called_once_with(self.anomaly_id, self.source)
            mock_rollback.finalize_epic_restoration.assert_called_once()
            self.assertTrue(status.get("success"))
            self.assertEqual(status.get("epic_summary"), epic_summary)


if __name__ == "__main__":
    unittest.main()