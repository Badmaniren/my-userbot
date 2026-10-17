import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.patch_auto_remediator import PatchAutoRemediator, PatchAutoRemediatorError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError
from skills.autonomous_engine import AutonomousEngineError


class TestPatchAutoRemediator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.max_commits = random.randint(1, 100)

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_success(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate.return_value = eval_result_mock

        engine_instance = mock_autonomous_engine_cls.return_value
        expected_cycle_result = {uuid.uuid4().hex: random.choice([True, False])}
        engine_instance.run_cycle.return_value = expected_cycle_result

        remediator = PatchAutoRemediator(repo_path=self.repo_path)
        result = remediator.remediate(self.patch_content, max_commits=self.max_commits)

        mock_patch_evaluator_cls.assert_called_once_with(repo_path=self.repo_path)
        evaluator_instance.evaluate.assert_called_once_with(self.patch_content)
        
        mock_autonomous_engine_cls.assert_called_once()
        engine_instance.run_cycle.assert_called_once_with(max_commits=self.max_commits)
        
        self.assertEqual(result, expected_cycle_result)

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_unsafe_patch(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = False
        eval_result_mock.is_valid = True
        
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate.return_value = eval_result_mock

        engine_instance = mock_autonomous_engine_cls.return_value

        remediator = PatchAutoRemediator(repo_path=self.repo_path)
        
        with self.assertRaises(PatchAutoRemediatorError) as ctx:
            remediator.remediate(self.patch_content, max_commits=self.max_commits)

        self.assertIn("unsafe", str(ctx.exception).lower())
        engine_instance.run_cycle.assert_not_called()

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_invalid_patch(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = False
        
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate.return_value = eval_result_mock

        engine_instance = mock_autonomous_engine_cls.return_value

        remediator = PatchAutoRemediator(repo_path=self.repo_path)
        
        with self.assertRaises(PatchAutoRemediatorError) as ctx:
            remediator.remediate(self.patch_content, max_commits=self.max_commits)

        self.assertIn("invalid", str(ctx.exception).lower())
        engine_instance.run_cycle.assert_not_called()

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_evaluator_raises_error(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate.side_effect = PatchEvaluatorError(uuid.uuid4().hex)

        remediator = PatchAutoRemediator(repo_path=self.repo_path)

        with self.assertRaises(PatchAutoRemediatorError):
            remediator.remediate(self.patch_content, max_commits=self.max_commits)

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_engine_raises_error(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate.return_value = eval_result_mock

        engine_instance = mock_autonomous_engine_cls.return_value
        engine_instance.run_cycle.side_effect = AutonomousEngineError(uuid.uuid4().hex)

        remediator = PatchAutoRemediator(repo_path=self.repo_path)

        with self.assertRaises(PatchAutoRemediatorError):
            remediator.remediate(self.patch_content, max_commits=self.max_commits)

    @patch('skills.patch_auto_remediator.PatchEvaluator')
    @patch('skills.patch_auto_remediator.AutonomousEngine')
    def test_remediate_stream(self, mock_autonomous_engine_cls, mock_patch_evaluator_cls):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        
        evaluator_instance = mock_patch_evaluator_cls.return_value
        evaluator_instance.evaluate_stream.return_value = eval_result_mock

        engine_instance = mock_autonomous_engine_cls.return_value
        expected_loop_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        engine_instance.run_autonomous_loop.return_value = expected_loop_result

        stream_data = io.BytesIO(self.patch_content.encode('utf-8'))

        remediator = PatchAutoRemediator(repo_path=self.repo_path)
        result = remediator.remediate_stream(stream_data)

        evaluator_instance.evaluate_stream.assert_called_once_with(stream_data)
        engine_instance.run_autonomous_loop.assert_called_once()
        self.assertEqual(result, expected_loop_result)


if __name__ == '__main__':
    unittest.main()