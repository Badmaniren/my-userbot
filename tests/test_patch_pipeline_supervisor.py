import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.patch_pipeline_supervisor import PatchPipelineSupervisor, PatchPipelineSupervisorError
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_verifier import PatchExecutorError


class TestPatchPipelineSupervisor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.analyzer_mock = MagicMock()
        self.verifier_mock = MagicMock()
        self.supervisor = PatchPipelineSupervisor(
            repo_path=self.repo_path,
            analyzer=self.analyzer_mock,
            verifier=self.verifier_mock
        )

    def test_run_pipeline_success(self):
        diff_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": diff_text,
            "target": f"{uuid.uuid4().hex}.py"
        }

        self.analyzer_mock.analyze.return_value = {"status": uuid.uuid4().hex}
        self.verifier_mock.verify_and_apply.return_value = True

        result = self.supervisor.run_pipeline(patch_data)

        self.assertTrue(result)
        self.analyzer_mock.analyze.assert_called_once_with(diff_text)
        self.verifier_mock.verify_and_apply.assert_called_once_with(patch_data)

    def test_run_pipeline_analyzer_error(self):
        diff_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": diff_text,
            "target": f"{uuid.uuid4().hex}.py"
        }
        err_msg = uuid.uuid4().hex
        self.analyzer_mock.analyze.side_effect = PatchAnalyzerError(err_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_pipeline(patch_data)

        self.assertIn(err_msg, str(ctx.exception))
        self.verifier_mock.verify_and_apply.assert_not_called()

    def test_run_pipeline_verifier_error(self):
        diff_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": diff_text,
            "target": f"{uuid.uuid4().hex}.py"
        }
        err_msg = uuid.uuid4().hex
        self.analyzer_mock.analyze.return_value = {"status": uuid.uuid4().hex}
        self.verifier_mock.verify_and_apply.side_effect = PatchExecutorError(err_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_pipeline(patch_data)

        self.assertIn(err_msg, str(ctx.exception))
        self.analyzer_mock.analyze.assert_called_once_with(diff_text)

    def test_run_stream_pipeline_success(self):
        stream_data = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(stream_data)
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}",
            "target": f"{uuid.uuid4().hex}.py"
        }

        self.analyzer_mock.analyze_stream.return_value = {"analyzed": True}
        self.verifier_mock.verify_and_apply.return_value = True

        result = self.supervisor.run_stream_pipeline(stream, patch_data)

        self.assertTrue(result)
        self.analyzer_mock.analyze_stream.assert_called_once_with(stream)
        self.verifier_mock.verify_and_apply.assert_called_once_with(patch_data)

    def test_run_stream_pipeline_analyzer_error(self):
        stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}",
            "target": f"{uuid.uuid4().hex}.py"
        }
        err_msg = uuid.uuid4().hex
        self.analyzer_mock.analyze_stream.side_effect = PatchAnalyzerError(err_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_stream_pipeline(stream, patch_data)

        self.assertIn(err_msg, str(ctx.exception))
        self.verifier_mock.verify_and_apply.assert_not_called()

    def test_run_stream_pipeline_verifier_error(self):
        stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        patch_data = {
            "id": uuid.uuid4().hex,
            "diff": f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}",
            "target": f"{uuid.uuid4().hex}.py"
        }
        err_msg = uuid.uuid4().hex
        self.analyzer_mock.analyze_stream.return_value = {"analyzed": True}
        self.verifier_mock.verify_and_apply.side_effect = PatchExecutorError(err_msg)

        with self.assertRaises(PatchPipelineSupervisorError) as ctx:
            self.supervisor.run_stream_pipeline(stream, patch_data)

        self.assertIn(err_msg, str(ctx.exception))
        self.analyzer_mock.analyze_stream.assert_called_once_with(stream)

    def test_process_patch_success(self):
        diff_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        session_id = uuid.uuid4().hex
        target_file = f"{uuid.uuid4().hex}.py"

        statistics_mock = {uuid.uuid4().hex: random.randint(1, 100)}
        self.analyzer_mock.analyze.return_value = statistics_mock
        self.verifier_mock.verify_and_apply.return_value = True

        result = self.supervisor.process_patch(diff_text, session_id, target_file)

        self.assertEqual(result["analyzed"], True)
        self.assertEqual(result["verified"], True)
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["statistics"], statistics_mock)

        expected_patch_data = {
            "id": session_id,
            "diff": diff_text,
            "target": target_file
        }
        self.analyzer_mock.analyze.assert_called_once_with(diff_text)
        self.verifier_mock.verify_and_apply.assert_called_once_with(expected_patch_data)


if __name__ == "__main__":
    unittest.main()