import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.autonomous_engine import AutonomousEngine, AutonomousEngineError
from skills.hypothesis_generator import HypothesisGeneratorError
from skills.patch_executor import PatchExecutorError


class TestAutonomousEngine(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.max_commits = random.randint(1, 50)

        with patch("skills.autonomous_engine.GitInspector") as mock_git, \
             patch("skills.autonomous_engine.LessonParser") as mock_lesson, \
             patch("skills.autonomous_engine.HypothesisGenerator") as mock_hypo, \
             patch("skills.autonomous_engine.PatchExecutor") as mock_exec:

            self.mock_git_instance = mock_git.return_value
            self.mock_lesson_instance = mock_lesson.return_value
            self.mock_hypo_instance = mock_hypo.return_value
            self.mock_exec_instance = mock_exec.return_value

            self.engine = AutonomousEngine(repo_path=self.repo_path)

    def test_initialization_composes_skills(self):
        self.assertIsNotNone(self.engine.git_inspector)
        self.assertIsNotNone(self.engine.lesson_parser)
        self.assertIsNotNone(self.engine.hypothesis_generator)
        self.assertIsNotNone(self.engine.patch_executor)

    def test_run_autonomous_cycle_success(self):
        random_hypothesis_id = uuid.uuid4().hex
        random_description = "".join(random.choices(string.ascii_letters, k=15))

        generated_hypotheses = [
            {"id": random_hypothesis_id, "description": random_description}
        ]
        prioritized_hypotheses = list(generated_hypotheses)

        random_result_key = uuid.uuid4().hex
        random_result_value = uuid.uuid4().hex
        execution_results = {random_result_key: random_result_value}

        self.mock_hypo_instance.generate_hypotheses.return_value = generated_hypotheses
        self.mock_hypo_instance.prioritize_hypotheses.return_value = prioritized_hypotheses
        self.mock_exec_instance.execute_from_lessons.return_value = execution_results

        result = self.engine.run_autonomous_cycle(max_commits=self.max_commits)

        self.mock_hypo_instance.generate_hypotheses.assert_called_once_with(self.max_commits)
        self.mock_hypo_instance.prioritize_hypotheses.assert_called_once_with(generated_hypotheses)
        self.mock_exec_instance.execute_from_lessons.assert_called_once()

        self.assertEqual(result, execution_results)
        self.assertIn(random_result_key, result)
        self.assertEqual(result[random_result_key], random_result_value)

    def test_run_autonomous_cycle_hypothesis_generator_error(self):
        random_error_msg = "".join(random.choices(string.ascii_letters, k=20))
        self.mock_hypo_instance.generate_hypotheses.side_effect = HypothesisGeneratorError(random_error_msg)

        with self.assertRaises(AutonomousEngineError) as ctx:
            self.engine.run_autonomous_cycle(max_commits=self.max_commits)

        self.assertIn(random_error_msg, str(ctx.exception))

    def test_run_autonomous_cycle_patch_executor_error(self):
        random_hypothesis_id = uuid.uuid4().hex
        generated_hypotheses = [{"id": random_hypothesis_id}]
        self.mock_hypo_instance.generate_hypotheses.return_value = generated_hypotheses
        self.mock_hypo_instance.prioritize_hypotheses.return_value = generated_hypotheses

        random_error_msg = "".join(random.choices(string.ascii_letters, k=25))
        self.mock_exec_instance.execute_from_lessons.side_effect = PatchExecutorError(random_error_msg)

        with self.assertRaises(AutonomousEngineError) as ctx:
            self.engine.run_autonomous_cycle(max_commits=self.max_commits)

        self.assertIn(random_error_msg, str(ctx.exception))

    def test_analyze_and_patch_specific_hypothesis(self):
        random_patch_id = uuid.uuid4().hex
        random_file_path = f"src/{uuid.uuid4().hex}.py"
        random_code = "".join(random.choices(string.printable, k=50))

        patch_data = {
            "id": random_patch_id,
            "file": random_file_path,
            "content": random_code
        }

        expected_success = random.choice([True, False])
        self.mock_exec_instance.apply_patch.return_value = expected_success

        result = self.engine.apply_specific_patch(patch_data)

        self.mock_exec_instance.apply_patch.assert_called_once_with(patch_data)
        self.assertEqual(result, expected_success)

    def test_rollback_operation(self):
        random_file = f"modules/{uuid.uuid4().hex}.py"
        random_commit = uuid.uuid4().hex
        expected_rollback_status = random.choice([True, False])

        self.mock_exec_instance.rollback_patch.return_value = expected_rollback_status

        result = self.engine.rollback_latest_patch(file_path=random_file, commit_hash=random_commit)

        self.mock_exec_instance.rollback_patch.assert_called_once_with(random_file, random_commit)
        self.assertEqual(result, expected_rollback_status)


if __name__ == "__main__":
    unittest.main()