import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_auto_remediator import PatchAutoRemediator, PatchAutoRemediatorError
from skills.patch_evaluator import PatchEvaluatorError, PatchEvaluationResult
from skills.autonomous_engine import AutonomousEngineError


class TestPatchAutoRemediatorInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.remediator = PatchAutoRemediator(repo_path=self.repo_path)
        self.rand_patch = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.max_commits_val = random.randint(1, 500)
        self.target_file_val = f"file_{uuid.uuid4().hex}.py"

    def test_remediate_success_without_target_file(self):
        expected_result = f"success_{uuid.uuid4().hex}"
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)

        with patch.object(self.remediator.patch_evaluator, 'evaluate', return_value=eval_result) as mock_eval, \
             patch.object(self.remediator.autonomous_engine, 'run_cycle', return_value=expected_result) as mock_cycle:

            res = self.remediator.remediate(self.rand_patch, max_commits=self.max_commits_val)

            mock_eval.assert_called_once_with(self.rand_patch)
            mock_cycle.assert_called_once_with(max_commits=self.max_commits_val)
            self.assertEqual(res, expected_result)

    def test_remediate_success_with_target_file(self):
        expected_result = f"success_{uuid.uuid4().hex}"
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)

        with patch.object(self.remediator.patch_evaluator, 'evaluate', return_value=eval_result) as mock_eval, \
             patch.object(self.remediator.autonomous_engine, 'run_cycle', return_value=expected_result) as mock_cycle:

            res = self.remediator.remediate(
                patch_content=self.rand_patch,
                max_commits=self.max_commits_val,
                target_file=self.target_file_val
            )

            mock_eval.assert_called_once_with(self.rand_patch)
            mock_cycle.assert_called_once_with(max_commits=self.max_commits_val, target_file=self.target_file_val)
            self.assertEqual(res, expected_result)

    def test_remediate_evaluator_error_raises_custom(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.remediator.patch_evaluator, 'evaluate', side_effect=PatchEvaluatorError(err_msg)) as mock_eval:
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate(self.rand_patch)
            self.assertIn(err_msg, str(ctx.exception))
            mock_eval.assert_called_once_with(self.rand_patch)

    def test_remediate_unsafe_patch_raises_custom(self):
        eval_result = PatchEvaluationResult(is_safe=False, is_valid=True)
        with patch.object(self.remediator.patch_evaluator, 'evaluate', return_value=eval_result):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate(self.rand_patch)
            self.assertIn("unsafe", str(ctx.exception).lower())

    def test_remediate_invalid_patch_raises_custom(self):
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=False)
        with patch.object(self.remediator.patch_evaluator, 'evaluate', return_value=eval_result):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate(self.rand_patch)
            self.assertIn("invalid", str(ctx.exception).lower())

    def test_remediate_engine_error_raises_custom(self):
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)
        engine_err_msg = uuid.uuid4().hex
        with patch.object(self.remediator.patch_evaluator, 'evaluate', return_value=eval_result), \
             patch.object(self.remediator.autonomous_engine, 'run_cycle', side_effect=AutonomousEngineError(engine_err_msg)):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate(self.rand_patch)
            self.assertIn(engine_err_msg, str(ctx.exception))

    def test_remediate_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)
        expected_loop_res = f"loop_res_{uuid.uuid4().hex}"
        kwargs = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.remediator.patch_evaluator, 'evaluate_stream', return_value=eval_result) as mock_stream_eval, \
             patch.object(self.remediator.autonomous_engine, 'run_autonomous_loop', return_value=expected_loop_res) as mock_loop:

            res = self.remediator.remediate_stream(stream_data, **kwargs)

            mock_stream_eval.assert_called_once_with(stream_data)
            mock_loop.assert_called_once_with(**kwargs)
            self.assertEqual(res, expected_loop_res)

    def test_remediate_stream_evaluator_error(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        err_msg = uuid.uuid4().hex
        with patch.object(self.remediator.patch_evaluator, 'evaluate_stream', side_effect=PatchEvaluatorError(err_msg)):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate_stream(stream_data)
            self.assertIn(err_msg, str(ctx.exception))

    def test_remediate_stream_unsafe_raises(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        eval_result = PatchEvaluationResult(is_safe=False, is_valid=True)
        with patch.object(self.remediator.patch_evaluator, 'evaluate_stream', return_value=eval_result):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate_stream(stream_data)
            self.assertIn("unsafe", str(ctx.exception).lower())

    def test_remediate_stream_invalid_raises(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=False)
        with patch.object(self.remediator.patch_evaluator, 'evaluate_stream', return_value=eval_result):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate_stream(stream_data)
            self.assertIn("invalid", str(ctx.exception).lower())

    def test_remediate_stream_engine_loop_error(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)
        engine_err_msg = uuid.uuid4().hex
        with patch.object(self.remediator.patch_evaluator, 'evaluate_stream', return_value=eval_result), \
             patch.object(self.remediator.autonomous_engine, 'run_autonomous_loop', side_effect=AutonomousEngineError(engine_err_msg)):
            with self.assertRaises(PatchAutoRemediatorError) as ctx:
                self.remediator.remediate_stream(stream_data)
            self.assertIn(engine_err_msg, str(ctx.exception))

    def test_aliases_presence(self):
        self.assertEqual(self.remediator.evaluator, self.remediator.patch_evaluator)
        self.assertEqual(self.remediator.engine, self.remediator.autonomous_engine)


if __name__ == '__main__':
    unittest.main()