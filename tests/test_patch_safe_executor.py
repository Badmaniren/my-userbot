import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.patch_safe_executor import PatchSafeExecutor, PatchSafeExecutorError
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_verifier import PatchVerifier


class TestPatchSafeExecutor(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.rand_diff = f"diff --git a/{uuid.uuid4().hex[:6]}.py b/{uuid.uuid4().hex[:6]}.py\nindex {uuid.uuid4().hex[:7]}..{uuid.uuid4().hex[:7]} 100644\n--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.rand_patch_data = {
            "diff": self.rand_diff,
            "target": f"module_{uuid.uuid4().hex[:6]}.py",
            "checksum": uuid.uuid4().hex
        }

    def test_safe_executor_initialization(self):
        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            executor = PatchSafeExecutor(self.rand_repo)

            self.assertEqual(executor.repo_path, self.rand_repo)
            mock_analyzer_cls.assert_called_once()
            mock_verifier_cls.assert_called_once()

    def test_execute_success_flow(self):
        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            mock_analyzer = mock_analyzer_cls.return_value
            mock_analyzer.analyze.return_value = {"status": "clean", "risks": []}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.return_value = True

            executor = PatchSafeExecutor(self.rand_repo)
            result = executor.execute(self.rand_patch_data)

            self.assertTrue(result)
            mock_analyzer.analyze.assert_called_once_with(self.rand_patch_data["diff"])
            mock_verifier.verify_and_apply.assert_called_once_with(self.rand_patch_data)

    def test_execute_analysis_failure_raises_error(self):
        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            mock_analyzer = mock_analyzer_cls.return_value
            rand_error_msg = f"Analysis failed: {uuid.uuid4().hex}"
            mock_analyzer.analyze.side_effect = PatchAnalyzerError(rand_error_msg)

            executor = PatchSafeExecutor(self.rand_repo)

            with self.assertRaises(PatchSafeExecutorError) as ctx:
                executor.execute(self.rand_patch_data)

            self.assertIn(rand_error_msg, str(ctx.exception))
            mock_verifier_cls.return_value.verify_and_apply.assert_not_called()

    def test_execute_syntax_risks_detected(self):
        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            mock_analyzer = mock_analyzer_cls.return_value
            rand_risk = f"RISK_{uuid.uuid4().hex[:6]}"
            mock_analyzer.analyze.return_value = {"status": "unsafe", "risks": [rand_risk]}

            executor = PatchSafeExecutor(self.rand_repo)

            with self.assertRaises(PatchSafeExecutorError) as ctx:
                executor.execute(self.rand_patch_data)

            self.assertIn(rand_risk, str(ctx.exception))
            mock_verifier_cls.return_value.verify_and_apply.assert_not_called()

    def test_execute_verification_rejection(self):
        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            mock_analyzer = mock_analyzer_cls.return_value
            mock_analyzer.analyze.return_value = {"status": "clean", "risks": []}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.return_value = False

            executor = PatchSafeExecutor(self.rand_repo)
            result = executor.execute(self.rand_patch_data)

            self.assertFalse(result)

    def test_execute_stream_input(self):
        rand_stream_data = f"stream_diff_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)

        with patch('skills.patch_safe_executor.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_safe_executor.PatchVerifier') as mock_verifier_cls:

            mock_analyzer = mock_analyzer_cls.return_value
            mock_analyzer.analyze_stream.return_value = {"status": "clean", "risks": []}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.return_value = True

            executor = PatchSafeExecutor(self.rand_repo)
            result = executor.execute_stream(mock_stream)

            self.assertTrue(result)
            mock_analyzer.analyze_stream.assert_called_once_with(mock_stream)


if __name__ == '__main__':
    unittest.main()
