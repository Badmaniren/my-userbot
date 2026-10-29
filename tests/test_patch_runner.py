import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_runner import PatchRunner, PatchRunnerError

class TestPatchRunnerInquisitor(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}"
        self.patch_data_val = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n--- a/{uuid.uuid4().hex}\n+++ b/{uuid.uuid4().hex}\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.commit_hash_val = uuid.uuid4().hex
        self.metric_name_val = f"metric_{uuid.uuid4().hex}"
        self.metric_val = random.uniform(0.0, 100.0)

    def test_patch_runner_initialization_chaos(self):
        runner = PatchRunner(repo_path=self.repo_path_val)
        self.assertEqual(runner.repo_path, self.repo_path_val)

    @patch('skills.patch_runner.PatchAnalyzer')
    @patch('skills.patch_runner.PatchApplier')
    @patch('skills.patch_runner.PatchChecker')
    @patch('skills.patch_runner.AnomalyAuditHub')
    def test_run_pipeline_success_flow(self, mock_audit_hub_cls, mock_checker_cls, mock_applier_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.return_value = True

        mock_checker = mock_checker_cls.return_value
        mock_checker.check.return_value = True

        runner = PatchRunner(repo_path=self.repo_path_val)
        result = runner.run_pipeline(self.patch_data_val)

        self.assertTrue(result)
        mock_analyzer.analyze.assert_called_once()
        mock_applier.apply_patch.assert_called_once()
        mock_checker.check.assert_called_once()

    @patch('skills.patch_runner.PatchAnalyzer')
    def test_run_pipeline_analyzer_failure(self, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        unique_error_msg = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = Exception(unique_error_msg)

        runner = PatchRunner(repo_path=self.repo_path_val)

        with self.assertRaises(PatchRunnerError) as ctx:
            runner.run_pipeline(self.patch_data_val)

        self.assertIn(unique_error_msg, str(ctx.exception))

    @patch('skills.patch_runner.PatchAnalyzer')
    @patch('skills.patch_runner.PatchApplier')
    def test_run_pipeline_applier_failure_triggers_rollback(self, mock_applier_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_applier = mock_applier_cls.return_value
        unique_error_msg = uuid.uuid4().hex
        mock_applier.apply_patch.side_effect = Exception(unique_error_msg)

        runner = PatchRunner(repo_path=self.repo_path_val)

        with self.assertRaises(PatchRunnerError) as ctx:
            runner.run_pipeline(self.patch_data_val)

        self.assertIn(unique_error_msg, str(ctx.exception))

    @patch('skills.patch_runner.PatchAnalyzer')
    @patch('skills.patch_runner.PatchApplier')
    @patch('skills.patch_runner.AnomalyAuditHub')
    def test_audit_hub_integration_during_pipeline(self, mock_audit_hub_cls, mock_applier_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.return_value = True

        mock_audit = mock_audit_hub_cls.return_value

        runner = PatchRunner(repo_path=self.repo_path_val)
        runner.run_pipeline(self.patch_data_val)

        mock_audit.log_anomaly.assert_called()

    @patch('skills.patch_runner.GitInspector')
    def test_git_inspector_integration_malformed_patch(self, mock_git_inspector_cls):
        mock_inspector = mock_git_inspector_cls.return_value
        mock_inspector.get_latest_changes.return_value = io.BytesIO(self.patch_data_val.encode('utf-8'))

        runner = PatchRunner(repo_path=self.repo_path_val)
        changes = runner.fetch_latest_repo_changes()

        self.assertIsNotNone(changes)
        mock_inspector.get_latest_changes.assert_called_once()

    @patch('skills.patch_runner.PatchSanitizer')
    def test_patch_sanitization_stage(self, mock_sanitizer_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        sanitized_payload = uuid.uuid4().hex
        mock_sanitizer.sanitize.return_value = sanitized_payload

        runner = PatchRunner(repo_path=self.repo_path_val)
        result = runner.sanitize_incoming_patch(self.patch_data_val)

        self.assertEqual(result, sanitized_payload)
        mock_sanitizer.sanitize.assert_called_once_with(self.patch_data_val)

    def test_patch_runner_error_inheritance(self):
        self.assertTrue(issubclass(PatchRunnerError, Exception))

if __name__ == '__main__':
    unittest.main()
