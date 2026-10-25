import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.anomaly_autofixer_worker import (
    AnomalyAutofixerWorker,
    AutofixerWorkerError,
    PatchApplicationError
)


class TestAnomalyAutofixerWorker(unittest.TestCase):

    def setUp(self):
        self.worker_id = uuid.uuid4().hex
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.log_path = f"/var/log/autofixer_{uuid.uuid4().hex}.log"
        self.worker = AnomalyAutofixerWorker(
            worker_id=self.worker_id,
            repo_path=self.repo_path,
            log_path=self.log_path
        )

    def test_initialization(self):
        self.assertEqual(self.worker.worker_id, self.worker_id)
        self.assertEqual(self.worker.repo_path, self.repo_path)
        self.assertEqual(self.worker.log_path, self.log_path)
        self.assertFalse(self.worker.is_running)

    def test_apply_patch_success(self):
        patch_id = uuid.uuid4().hex
        target_file = f"src/modules/{uuid.uuid4().hex}.py"
        patch_content = f"diff --git a/{target_file} b/{target_file}\n+" + "".join(random.choices(string.ascii_letters, k=25))

        mock_subprocess_result = MagicMock()
        mock_subprocess_result.returncode = 0
        mock_subprocess_result.stdout = f"Patch applied successfully for {patch_id}".encode('utf-8')

        with patch('subprocess.run', return_value=mock_subprocess_result) as mock_run:
            result = self.worker.apply_patch(patch_id=patch_id, patch_content=patch_content, target_file=target_file)
            
            self.assertTrue(result)
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            self.assertIn("git", args[0])

    def test_apply_patch_failure(self):
        patch_id = uuid.uuid4().hex
        target_file = f"core/{uuid.uuid4().hex}.py"
        err_msg = f"Rejected patch hunk {uuid.uuid4().hex}"

        mock_subprocess_result = MagicMock()
        mock_subprocess_result.returncode = 1
        mock_subprocess_result.stderr = err_msg.encode('utf-8')

        with patch('subprocess.run', return_value=mock_subprocess_result):
            with self.assertRaises(PatchApplicationError) as ctx:
                self.worker.apply_patch(patch_id=patch_id, patch_content="invalid diff", target_file=target_file)
            self.assertIn(patch_id, str(ctx.exception))

    def test_verify_fix_success(self):
        anomaly_id = uuid.uuid4().hex
        test_command = f"pytest tests/test_{uuid.uuid4().hex}.py"

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = io.BytesIO(f"OK {uuid.uuid4().hex}".encode('utf-8'))

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            success = self.worker.verify_fix(anomaly_id=anomaly_id, verification_command=test_command)
            self.assertTrue(success)
            mock_popen.assert_called_once()

    def test_verify_fix_failure(self):
        anomaly_id = uuid.uuid4().hex
        test_command = f"nosetests {uuid.uuid4().hex}"

        mock_process = MagicMock()
        mock_process.returncode = random.randint(1, 255)
        mock_process.stdout = io.BytesIO(f"FAIL {uuid.uuid4().hex}".encode('utf-8'))

        with patch('subprocess.Popen', return_value=mock_process):
            success = self.worker.verify_fix(anomaly_id=anomaly_id, verification_command=test_command)
            self.assertFalse(success)

    def test_rollback_patch(self):
        commit_hash = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            res = self.worker.rollback_patch(commit_hash=commit_hash)
            self.assertTrue(res)
            called_cmd = mock_run.call_args[0][0]
            self.assertIn(commit_hash, called_cmd)

    def test_process_autofix_workflow_complete(self):
        anomaly_id = uuid.uuid4().hex
        patch_id = uuid.uuid4().hex
        target_file = f"services/{uuid.uuid4().hex}.py"
        patch_content = f"+print('{uuid.uuid4().hex}')"
        verify_cmd = f"python -m unittest test_{uuid.uuid4().hex}.py"

        with patch.object(self.worker, 'apply_patch', return_value=True) as mock_apply, \
             patch.object(self.worker, 'verify_fix', return_value=True) as mock_verify:
            
            status = self.worker.process_autofix(
                anomaly_id=anomaly_id,
                patch_id=patch_id,
                patch_content=patch_content,
                target_file=target_file,
                verification_command=verify_cmd
            )

            self.assertEqual(status, "RESOLVED")
            mock_apply.assert_called_once_with(patch_id, patch_content, target_file)
            mock_verify.assert_called_once_with(anomaly_id, verify_cmd)

    def test_process_autofix_workflow_verification_fails_triggers_rollback(self):
        anomaly_id = uuid.uuid4().hex
        patch_id = uuid.uuid4().hex
        target_file = f"components/{uuid.uuid4().hex}.py"
        patch_content = f"-broken\n+fixed_{uuid.uuid4().hex}"
        verify_cmd = f"pytest {uuid.uuid4().hex}"
        last_commit = uuid.uuid4().hex

        with patch.object(self.worker, 'apply_patch', return_value=True), \
             patch.object(self.worker, 'verify_fix', return_value=False), \
             patch.object(self.worker, '_get_current_commit_hash', return_value=last_commit), \
             patch.object(self.worker, 'rollback_patch', return_value=True) as mock_rollback:

            status = self.worker.process_autofix(
                anomaly_id=anomaly_id,
                patch_id=patch_id,
                patch_content=patch_content,
                target_file=target_file,
                verification_command=verify_cmd
            )

            self.assertEqual(status, "ROLLED_BACK")
            mock_rollback.assert_called_once_with(last_commit)

    def test_log_action(self):
        action_name = uuid.uuid4().hex
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            self.worker.log_action(action_name, payload)
            mock_open.assert_called_once_with(self.log_path, 'a', encoding='utf-8')
            mock_file.__enter__().write.assert_called_once()