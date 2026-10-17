import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.patch_pipeline_supervisor import PatchPipelineSupervisor, PatchPipelineSupervisorError
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_verifier import PatchVerifierError


class TestPatchPipelineSupervisor(unittest.TestCase):

    def setUp(self):
        self.rand_repo_dir = f"/tmp/{uuid.uuid4().hex}"
        self.rand_diff_text = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\nindex {uuid.uuid4().hex[:7]}..{uuid.uuid4().hex[:7]} 100644\n--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.rand_patch_data = {
            "id": uuid.uuid4().hex,
            "diff": self.rand_diff_text,
            "target": f"{uuid.uuid4().hex}.py"
        }
        self.supervisor = PatchPipelineSupervisor(repo_path=self.rand_repo_dir)

    @patch('skills.patch_pipeline_supervisor.PatchAnalyzer')
    @patch('skills.patch_pipeline_supervisor.PatchVerifier')
    def test_pipeline_success_cycle(self, mock_verifier_cls, mock_analyzer_cls):
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        expected_analysis = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "syntax_risk": False
        }
        mock_analyzer_instance.analyze.return_value = expected_analysis
        mock_verifier_instance.verify_and_apply.return_value = True

        result = self.supervisor.run_pipeline(self.rand_patch_data)

        self.assertTrue(result)
        mock_analyzer_instance.analyze.assert_called_once_with(self.rand_patch_data["diff"])
        mock_verifier_instance.verify_and_apply.assert_called_once_with(self.rand_patch_data)

    @patch('skills.patch_pipeline_supervisor.PatchAnalyzer')
    @patch('skills.patch_pipeline_supervisor.PatchVerifier')
    def test_pipeline_analyzer_failure(self, mock_verifier_cls, mock_analyzer_cls):
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        rand_error_msg = uuid.uuid4().hex
        mock_analyzer_instance.analyze.side_effect = PatchAnalyzerError(rand_error_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_pipeline(self.rand_patch_data)

        self.assertIn(rand_error_msg, str(ctx.exception))
        mock_verifier_instance.verify_and_apply.assert_not_called()

    @patch('skills.patch_pipeline_supervisor.PatchAnalyzer')
    @patch('skills.patch_pipeline_supervisor.PatchVerifier')
    def test_pipeline_verifier_failure(self, mock_verifier_cls, mock_analyzer_cls):
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        mock_analyzer_instance.analyze.return_value = {"status": uuid.uuid4().hex}
        rand_verifier_msg = uuid.uuid4().hex
        mock_verifier_instance.verify_and_apply.side_effect = PatchVerifierError(rand_verifier_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_pipeline(self.rand_patch_data)

        self.assertIn(rand_verifier_msg, str(ctx.exception))
        mock_analyzer_instance.analyze.assert_called_once_with(self.rand_patch_data["diff"])
        mock_verifier_instance.verify_and_apply.assert_called_once_with(self.rand_patch_data)

    @patch('skills.patch_pipeline_supervisor.PatchAnalyzer')
    @patch('skills.patch_pipeline_supervisor.PatchVerifier')
    def test_pipeline_stream_processing(self, mock_verifier_cls, mock_analyzer_cls):
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        rand_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        stream_mock = io.BytesIO(rand_stream_data.encode('utf-8'))

        mock_analyzer_instance.analyze_stream.return_value = {uuid.uuid4().hex: True}
        mock_verifier_instance.verify_and_apply.return_value = True

        result = self.supervisor.run_stream_pipeline(stream_mock, self.rand_patch_data)

        self.assertTrue(result)
        mock_analyzer_instance.analyze_stream.assert_called_once()
        mock_verifier_instance.verify_and_apply.assert_called_once_with(self.rand_patch_data)


if __name__ == '__main__':
    unittest.main()