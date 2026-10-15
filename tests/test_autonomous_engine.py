import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.autonomous_engine import AutonomousEngine, AutonomousEngineError

class TestAutonomousEngine(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.max_commits = random.randint(1, 100)

    @patch('skills.autonomous_engine.HypothesisGenerator')
    @patch('skills.autonomous_engine.PatchExecutor')
    @patch('skills.autonomous_engine.PatchVerifier')
    @patch('skills.autonomous_engine.GitInspector')
    @patch('skills.autonomous_engine.LessonParser')
    def test_init_composition(self, mock_lesson_parser, mock_git_inspector, mock_patch_verifier, mock_patch_executor, mock_hypothesis_generator):
        engine = AutonomousEngine(self.repo_path)
        
        mock_git_inspector.assert_called_once_with(self.repo_path)
        mock_lesson_parser.assert_called_once()
        mock_hypothesis_generator.assert_called_once()
        mock_patch_executor.assert_called_once_with(
            self.repo_path, 
            mock_git_inspector.return_value, 
            mock_lesson_parser.return_value
        )
        mock_patch_verifier.assert_called_once_with(
            self.repo_path, 
            mock_git_inspector.return_value, 
            mock_patch_executor.return_value
        )

    @patch('skills.autonomous_engine.GitInspector')
    @patch('skills.autonomous_engine.LessonParser')
    @patch('skills.autonomous_engine.HypothesisGenerator')
    @patch('skills.autonomous_engine.PatchExecutor')
    @patch('skills.autonomous_engine.PatchVerifier')
    def test_run_autonomous_cycle_success(self, mock_verifier_cls, mock_executor_cls, mock_hypo_cls, mock_parser_cls, mock_inspector_cls):
        random_hypothesis_id = uuid.uuid4().hex
        random_description = ''.join(random.choices(string.ascii_letters, k=15))
        
        mock_hypo_instance = mock_hypo_cls.return_value
        mock_hypo_instance.generate_hypotheses.return_value = [{'id': random_hypothesis_id, 'desc': random_description}]
        mock_hypo_instance.prioritize_hypotheses.return_value = [{'id': random_hypothesis_id, 'desc': random_description}]

        mock_verifier_instance = mock_verifier_cls.return_value
        mock_verifier_instance.verify_and_apply.return_value = True

        engine = AutonomousEngine(self.repo_path)
        result = engine.run_cycle(max_commits=self.max_commits)

        mock_hypo_instance.generate_hypotheses.assert_called_once_with(self.max_commits)
        mock_hypo_instance.prioritize_hypotheses.assert_called_once()
        mock_verifier_instance.verify_and_apply.assert_called_once_with({'id': random_hypothesis_id, 'desc': random_description})
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('applied_hypothesis')['id'], random_hypothesis_id)

    @patch('skills.autonomous_engine.GitInspector')
    @patch('skills.autonomous_engine.LessonParser')
    @patch('skills.autonomous_engine.HypothesisGenerator')
    @patch('skills.autonomous_engine.PatchExecutor')
    @patch('skills.autonomous_engine.PatchVerifier')
    def test_run_autonomous_cycle_no_hypotheses(self, mock_verifier_cls, mock_executor_cls, mock_hypo_cls, mock_parser_cls, mock_inspector_cls):
        mock_hypo_instance = mock_hypo_cls.return_value
        mock_hypo_instance.generate_hypotheses.return_value = []
        mock_hypo_instance.prioritize_hypotheses.return_value = []

        engine = AutonomousEngine(self.repo_path)
        result = engine.run_cycle(max_commits=self.max_commits)

        mock_verifier_cls.return_value.verify_and_apply.assert_not_called()
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get('success'))

    @patch('skills.autonomous_engine.GitInspector')
    @patch('skills.autonomous_engine.LessonParser')
    @patch('skills.autonomous_engine.HypothesisGenerator')
    @patch('skills.autonomous_engine.PatchExecutor')
    @patch('skills.autonomous_engine.PatchVerifier')
    def test_run_autonomous_cycle_verification_fails(self, mock_verifier_cls, mock_executor_cls, mock_hypo_cls, mock_parser_cls, mock_inspector_cls):
        random_hypothesis_id = uuid.uuid4().hex
        
        mock_hypo_instance = mock_hypo_cls.return_value
        mock_hypo_instance.generate_hypotheses.return_value = [{'id': random_hypothesis_id}]
        mock_hypo_instance.prioritize_hypotheses.return_value = [{'id': random_hypothesis_id}]

        mock_verifier_instance = mock_verifier_cls.return_value
        mock_verifier_instance.verify_and_apply.return_value = False

        engine = AutonomousEngine(self.repo_path)
        result = engine.run_cycle(max_commits=self.max_commits)

        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('failed_hypothesis')['id'], random_hypothesis_id)

    @patch('skills.autonomous_engine.GitInspector')
    @patch('skills.autonomous_engine.LessonParser')
    @patch('skills.autonomous_engine.HypothesisGenerator')
    @patch('skills.autonomous_engine.PatchExecutor')
    @patch('skills.autonomous_engine.PatchVerifier')
    def test_exception_handling_in_cycle(self, mock_verifier_cls, mock_executor_cls, mock_hypo_cls, mock_parser_cls, mock_inspector_cls):
        random_error_msg = uuid.uuid4().hex
        mock_hypo_instance = mock_hypo_cls.return_value
        mock_hypo_instance.generate_hypotheses.side_effect = Exception(random_error_msg)

        engine = AutonomousEngine(self.repo_path)
        
        with self.assertRaises(AutonomousEngineError) as ctx:
            engine.run_cycle(max_commits=self.max_commits)
            
        self.assertIn(random_error_msg, str(ctx.exception))