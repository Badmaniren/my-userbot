import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.patch_pipeline_orchestrator import PatchPipelineOrchestrator, PatchPipelineError


class TestPatchPipelineOrchestrator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.policy = random.choice(["strict", "lenient", "custom"])
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.orchestrator = PatchPipelineOrchestrator(
            repo_path=self.repo_path,
            policy=self.policy,
            backup_tag=self.backup_tag
        )

    @patch("skills.patch_pipeline_orchestrator.open")
    def test_process_patch_success(self, mock_open):
        patch_path = f"/patches/{uuid.uuid4().hex}.patch"
        target_file = f"src/{uuid.uuid4().hex}.py"
        file_content = f"content_{uuid.uuid4().hex}"

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = file_content
        mock_open.return_value = mock_file

        with patch.object(self.orchestrator, 'process_and_apply', return_value=True) as mock_process_and_apply:
            res = self.orchestrator.process_patch(patch_path, target_file)
            self.assertTrue(res)
            mock_open.assert_called_once_with(patch_path, 'r', encoding='utf-8')
            mock_process_and_apply.assert_called_once_with(file_content, target_file)

    def test_process_and_apply_success(self):
        patch_source = f"source_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        sanitized_content = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.orchestrator.sanitizer, 'sanitize', return_value=sanitized_content) as mock_sanitize, \
             patch.object(self.orchestrator.checker, 'check', return_value={"status": "passed"}) as mock_check, \
             patch.object(self.orchestrator.applier, 'create_recovery_point', return_value=True) as mock_recovery, \
             patch.object(self.orchestrator.applier, 'apply_patch', return_value=True) as mock_apply, \
             patch.object(self.orchestrator.applier, 'verify_repository_state', return_value=True) as mock_verify:

            result = self.orchestrator.process_and_apply(patch_source, target_file)

            self.assertTrue(result)
            mock_sanitize.assert_called_once_with(patch_source)
            mock_check.assert_called_once_with(sanitized_content, self.repo_path, target_file, self.policy)
            mock_recovery.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(sanitized_content)
            mock_verify.assert_called_once()

    def test_process_and_apply_check_failed(self):
        patch_source = f"source_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        sanitized_content = f"sanitized_{uuid.uuid4().hex}"
        failure_reason = f"reason_{uuid.uuid4().hex}"

        with patch.object(self.orchestrator.sanitizer, 'sanitize', return_value=sanitized_content), \
             patch.object(self.orchestrator.checker, 'check', return_value={"status": "failed", "reason": failure_reason}), \
             patch.object(self.orchestrator.applier, 'create_recovery_point') as mock_recovery:

            with self.assertRaises(PatchPipelineError) as ctx:
                self.orchestrator.process_and_apply(patch_source, target_file)

            self.assertIn(failure_reason, str(ctx.exception))
            mock_recovery.assert_not_called()

    def test_process_and_apply_recovery_point_failed(self):
        patch_source = f"source_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        sanitized_content = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.orchestrator.sanitizer, 'sanitize', return_value=sanitized_content), \
             patch.object(self.orchestrator.checker, 'check', return_value={"status": "passed"}), \
             patch.object(self.orchestrator.applier, 'create_recovery_point', return_value=False) as mock_recovery, \
             patch.object(self.orchestrator.applier, 'rollback') as mock_rollback:

            with self.assertRaises(PatchPipelineError) as ctx:
                self.orchestrator.process_and_apply(patch_source, target_file)

            self.assertIn("Failed to create recovery point", str(ctx.exception))
            mock_recovery.assert_called_once_with(self.backup_tag)
            mock_rollback.assert_not_called()

    def test_process_and_apply_apply_patch_failed(self):
        patch_source = f"source_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        sanitized_content = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.orchestrator.sanitizer, 'sanitize', return_value=sanitized_content), \
             patch.object(self.orchestrator.checker, 'check', return_value={"status": "passed"}), \
             patch.object(self.orchestrator.applier, 'create_recovery_point', return_value=True), \
             patch.object(self.orchestrator.applier, 'apply_patch', return_value=False), \
             patch.object(self.orchestrator.applier, 'rollback', return_value=True) as mock_rollback:

            with self.assertRaises(PatchPipelineError) as ctx:
                self.orchestrator.process_and_apply(patch_source, target_file)

            self.assertIn("Failed to apply patch", str(ctx.exception))
            mock_rollback.assert_called_once_with(self.backup_tag)

    def test_process_and_apply_verify_failed(self):
        patch_source = f"source_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        sanitized_content = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.orchestrator.sanitizer, 'sanitize', return_value=sanitized_content), \
             patch.object(self.orchestrator.checker, 'check', return_value={"status": "passed"}), \
             patch.object(self.orchestrator.applier, 'create_recovery_point', return_value=True), \
             patch.object(self.orchestrator.applier, 'apply_patch', return_value=True), \
             patch.object(self.orchestrator.applier, 'verify_repository_state', return_value=False), \
             patch.object(self.orchestrator.applier, 'rollback', return_value=True) as mock_rollback:

            with self.assertRaises(PatchPipelineError) as ctx:
                self.orchestrator.process_and_apply(patch_source, target_file)

            self.assertIn("Repository state verification failed", str(ctx.exception))
            mock_rollback.assert_called_once_with(self.backup_tag)


if __name__ == '__main__':
    unittest.main()