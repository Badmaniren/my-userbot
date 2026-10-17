import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_auto_remediator_pipeline import (
    PatchAutoRemediatorPipeline,
    PatchAutoRemediatorPipelineError
)
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_checker import PatchCheckerError

class TestPatchAutoRemediatorPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.target_file = f"src/{uuid.uuid4().hex}.py"
        self.policy = random.choice(["strict", "lenient", "custom_anticheat"])
        self.pipeline = PatchAutoRemediatorPipeline(repo_path=self.repo_path, policy=self.policy)

    def test_pipeline_initialization(self):
        rand_repo = f"/var/repo/{uuid.uuid4().hex}"
        rand_policy = f"policy_{uuid.uuid4().hex}"

        pipe = PatchAutoRemediatorPipeline(repo_path=rand_repo, policy=rand_policy)

        self.assertEqual(pipe.repo_path, rand_repo)
        self.assertEqual(pipe.policy, rand_policy)

    def test_run_pipeline_success(self):
        patch_content = f"diff --git a/{self.target_file} b/{self.target_file}\n+print('{uuid.uuid4().hex}')"

        mock_analysis_result = {
            "status": "clean",
            "risk_score": random.randint(0, 10),
            "signature": uuid.uuid4().hex
        }

        mock_check_result = {
            "verified": True,
            "violations": [],
            "token": uuid.uuid4().hex
        }

        with patch("skills.patch_auto_remediator_pipeline.PatchAnalyzer") as MockAnalyzerClass, \
             patch("skills.patch_auto_remediator_pipeline.PatchChecker") as MockCheckerClass:

            analyzer_instance = MockAnalyzerClass.return_value
            analyzer_instance.analyze.return_value = mock_analysis_result

            checker_instance = MockCheckerClass.return_value
            checker_instance.check_patch.return_value = mock_check_result

            result = self.pipeline.run(patch_content=patch_content, target_file=self.target_file)

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("analysis"), mock_analysis_result)
            self.assertEqual(result.get("verification"), mock_check_result)

            analyzer_instance.analyze.assert_called_once_with(patch_content)
            checker_instance.check_patch.assert_called_once_with(patch_content, self.target_file)

    def test_run_pipeline_analyzer_failure(self):
        patch_content = f"invalid_diff_{uuid.uuid4().hex}"
        error_message = f"analyzer_err_{uuid.uuid4().hex}"

        with patch("skills.patch_auto_remediator_pipeline.PatchAnalyzer") as MockAnalyzerClass, \
             patch("skills.patch_auto_remediator_pipeline.PatchChecker") as MockCheckerClass:

            analyzer_instance = MockAnalyzerClass.return_value
            analyzer_instance.analyze.side_effect = PatchAnalyzerError(error_message)

            with self.assertRaises(PatchAutoRemediatorPipelineError) as ctx:
                self.pipeline.run(patch_content=patch_content, target_file=self.target_file)

            self.assertIn(error_message, str(ctx.exception))
            MockCheckerClass.return_value.check_patch.assert_not_called()

    def test_run_pipeline_checker_failure(self):
        patch_content = f"diff --git a/{self.target_file} b/{self.target_file}\n+bad_code_{uuid.uuid4().hex}"
        error_message = f"checker_err_{uuid.uuid4().hex}"

        with patch("skills.patch_auto_remediator_pipeline.PatchAnalyzer") as MockAnalyzerClass, \
             patch("skills.patch_auto_remediator_pipeline.PatchChecker") as MockCheckerClass:

            analyzer_instance = MockAnalyzerClass.return_value
            analyzer_instance.analyze.return_value = {"status": "ok"}

            checker_instance = MockCheckerClass.return_value
            checker_instance.check_patch.side_effect = PatchCheckerError(error_message)

            with self.assertRaises(PatchAutoRemediatorPipelineError) as ctx:
                self.pipeline.run(patch_content=patch_content, target_file=self.target_file)

            self.assertIn(error_message, str(ctx.exception))

    def test_run_stream_pipeline_success(self):
        stream_data = f"stream_diff_{uuid.uuid4().hex}".encode('utf-8')
        stream_io = io.BytesIO(stream_data)

        expected_token = uuid.uuid4().hex

        with patch("skills.patch_auto_remediator_pipeline.PatchAnalyzer") as MockAnalyzerClass, \
             patch("skills.patch_auto_remediator_pipeline.PatchChecker") as MockCheckerClass:

            analyzer_instance = MockAnalyzerClass.return_value
            analyzer_instance.analyze_stream.return_value = {"stream_status": "passed"}

            checker_instance = MockCheckerClass.return_value
            checker_instance.check_stream.return_value = {"verified": True, "token": expected_token}

            result = self.pipeline.run_stream(stream=stream_io, target_file=self.target_file)

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("verification").get("token"), expected_token)
            analyzer_instance.analyze_stream.assert_called_once()
            checker_instance.check_stream.assert_called_once()

    def test_run_file_pipeline_security_violation(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.patch"
        violation_reason = f"anticheat_violation_{uuid.uuid4().hex}"

        mock_check_result = {
            "verified": False,
            "violations": [violation_reason]
        }

        with patch("skills.patch_auto_remediator_pipeline.PatchAnalyzer") as MockAnalyzerClass, \
             patch("skills.patch_auto_remediator_pipeline.PatchChecker") as MockCheckerClass:

            analyzer_instance = MockAnalyzerClass.return_value
            analyzer_instance.analyze_file.return_value = {"file_analyzed": True}

            checker_instance = MockCheckerClass.return_value
            checker_instance.check_file.return_value = mock_check_result

            result = self.pipeline.run_file(file_path=file_path, target_file=self.target_file)

            self.assertFalse(result.get("success"))
            self.assertIn(violation_reason, result.get("verification").get("violations"))

if __name__ == "__main__":
    unittest.main()