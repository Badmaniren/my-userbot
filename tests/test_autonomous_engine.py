import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills.autonomous_engine import AutonomousEngine


class TestAutonomousEngineInquisitor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.max_commits = random.randint(1, 100)
        self.engine = AutonomousEngine(repo_path=self.repo_path)

    def test_composition_imports_and_instantiation(self):
        self.assertTrue(hasattr(self.engine, 'git_inspector'))
        self.assertTrue(hasattr(self.engine, 'hypothesis_generator'))
        self.assertTrue(hasattr(self.engine, 'patch_executor'))
        self.assertTrue(hasattr(self.engine, 'lesson_parser'))

    def test_run_autonomous_cycle_success(self):
        expected_hypothesis = f"hyp_{uuid.uuid4().hex}"
        expected_patch_result = random.choice([True, False])

        with patch('skills.autonomous_engine.GitInspector') as MockGit, \
             patch('skills.autonomous_engine.LessonParser') as MockLesson, \
             patch('skills.autonomous_engine.HypothesisGenerator') as MockHypo, \
             patch('skills.autonomous_engine.PatchExecutor') as MockPatch:

            mock_git_instance = MockGit.return_value
            mock_lesson_instance = MockLesson.return_value
            mock_hypo_instance = MockHypo.return_value
            mock_patch_instance = MockPatch.return_value

            mock_hypo_instance.generate_hypotheses.return_value = [expected_hypothesis]
            mock_hypo_instance.prioritize_hypotheses.return_value = [expected_hypothesis]
            mock_patch_instance.apply_patch.return_value = expected_patch_result

            result = self.engine.run_cycle(max_commits=self.max_commits)

            MockGit.assert_called_once_with(self.repo_path)
            MockLesson.assert_called_once()
            MockHypo.assert_called_once()
            MockPatch.assert_called_once()

            mock_hypo_instance.generate_hypotheses.assert_called_once_with(self.max_commits)
            mock_hypo_instance.prioritize_hypotheses.assert_called_once_with([expected_hypothesis])
            mock_patch_instance.apply_patch.assert_called_once_with(expected_hypothesis)

            self.assertIn(expected_hypothesis, str(result))

    def test_run_autonomous_cycle_io_chaos_and_empty_hypotheses(self):
        random_error_msg = ''.join(random.choices(string.ascii_letters, k=15))

        with patch('skills.autonomous_engine.GitInspector'), \
             patch('skills.autonomous_engine.LessonParser'), \
             patch('skills.autonomous_engine.HypothesisGenerator') as MockHypo, \
             patch('skills.autonomous_engine.PatchExecutor'):

            mock_hypo_instance = MockHypo.return_value
            mock_hypo_instance.generate_hypotheses.side_effect = Exception(random_error_msg)

            with self.assertRaises(Exception) as ctx:
                self.engine.run_cycle(max_commits=self.max_commits)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_execute_from_lessons_integration(self):
        mock_execution_result = {
            "status": uuid.uuid4().hex,
            "applied": random.randint(0, 5)
        }

        with patch('skills.autonomous_engine.GitInspector'), \
             patch('skills.autonomous_engine.LessonParser'), \
             patch('skills.autonomous_engine.HypothesisGenerator'), \
             patch('skills.autonomous_engine.PatchExecutor') as MockPatch:

            mock_patch_instance = MockPatch.return_value
            mock_patch_instance.execute_from_lessons.return_value = mock_execution_result

            result = self.engine.execute_lessons_cycle()

            mock_patch_instance.execute_from_lessons.assert_called_once()
            self.assertEqual(result, mock_execution_result)

    def test_stream_data_handling_with_chaos(self):
        random_bytes = bytes(random.getrandbits(8) for _ in range(64))
        stream_mock = io.BytesIO(random_bytes)

        with patch('skills.autonomous_engine.GitInspector') as MockGit, \
             patch('skills.autonomous_engine.LessonParser'), \
             patch('skills.autonomous_engine.HypothesisGenerator'), \
             patch('skills.autonomous_engine.PatchExecutor'):

            mock_git_instance = MockGit.return_value
            mock_git_instance.read_file_at_commit.return_value = stream_mock

            random_commit = uuid.uuid4().hex
            random_file = f"{uuid.uuid4().hex}.py"

            data = self.engine.inspect_file_content(random_commit, random_file)

            mock_git_instance.read_file_at_commit.assert_called_once_with(random_commit, random_file)
            self.assertEqual(data.read(), random_bytes)


if __name__ == '__main__':
    unittest.main()