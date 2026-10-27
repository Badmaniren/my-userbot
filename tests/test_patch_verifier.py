import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import os

from skills.patch_verifier import (
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError,
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier
)

class TestPatchVerifierModule(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    @patch("subprocess.run")
    def class_git_inspector_methods(self, mock_run):
        random_hash = uuid.uuid4().hex
        random_author = uuid.uuid4().hex
        random_msg = uuid.uuid4().hex
        git_log_out = f"{random_hash}|{random_author}|{random_msg}\n"
        diff_out = uuid.uuid4().hex
        file_content = uuid.uuid4().hex

        def side_effect(cmd, *args, **kwargs):
            if "log" in cmd:
                return MagicMock(stdout=git_log_out)
            elif "show" in cmd:
                for arg in cmd:
                    if ":" in arg:
                        return MagicMock(stdout=file_content)
                return MagicMock(stdout=diff_out)
            return MagicMock(stdout="")

        mock_run.side_effect = side_effect

        history = self.inspector.get_commit_history(max_count=random.randint(1, 100))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], random_hash)
        self.assertEqual(history[0]["author"], random_author)
        self.assertEqual(history[0]["message"], random_msg)

        file_diff = self.inspector.get_file_diff(random_hash)
        self.assertEqual(file_diff, diff_out)

        analysis = self.inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"]["hash"], random_hash)

        file_data = self.inspector.read_file_at_commit(random_hash, "test.py")
        self.assertEqual(file_data, file_content)

        history_alias = self.inspector.get_history(max_count=5)
        self.assertEqual(len(history_alias), 1)

        latest_changes = self.inspector.get_latest_changes()
        self.assertEqual(latest_changes, diff_out)

    @patch("subprocess.run")
    def test_git_inspector_methods(self, mock_run):
        self.class_git_inspector_methods()

    def test_lesson_parser_methods(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertGreater(len(lessons), 0)

        extracted = self.parser.extract_lessons(max_commits=random.randint(5, 15))
        self.assertIn("lesson_id", extracted)
        self.assertIn("content", extracted)

    def test_hypothesis_generator_methods(self):
        hypotheses = self.generator.generate_hypotheses(max_commits=random.randint(1, 20))
        self.assertIsInstance(hypotheses, list)
        self.assertGreater(len(hypotheses), 0)

        rand_weight_1 = random.random()
        rand_weight_2 = rand_weight_1 + random.uniform(0.1, 0.5)
        test_hyps = [
            {"id": uuid.uuid4().hex, "weight": rand_weight_1},
            {"id": uuid.uuid4().hex, "weight": rand_weight_2}
        ]
        prioritized = self.generator.prioritize_hypotheses(test_hyps)
        self.assertEqual(prioritized[0]["weight"], rand_weight_2)
        self.assertEqual(prioritized[1]["weight"], rand_weight_1)

    @patch("subprocess.run")
    def test_patch_executor_apply_rollback(self, mock_run):
        file_path = f"{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        commit_msg = uuid.uuid4().hex

        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            success = self.executor.apply_patch(patch_data)
            self.assertTrue(success)
            mock_file.assert_called_once()

        bad_patch_data = {"file_path": "", "content": None}
        self.assertFalse(self.executor.apply_patch(bad_patch_data))

        commit_hash = uuid.uuid4().hex
        rollback_success = self.executor.rollback_patch(file_path, commit_hash)
        self.assertTrue(rollback_success)

        exec_lessons = self.executor.execute_from_lessons()
        self.assertIn("executed_lessons", exec_lessons)
        self.assertEqual(exec_lessons["status"], "success")

    @patch("subprocess.run")
    def test_patch_verifier_logic(self, mock_run):
        valid_content = f"def {uuid.uuid4().hex}(): pass"
        valid_patch = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": valid_content,
            "commit_message": uuid.uuid4().hex
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()):
            res_valid = self.verifier.verify_and_apply(valid_patch)
            self.assertTrue(res_valid)

            invalid_content = f"syntax error here {uuid.uuid4().hex}"
            invalid_patch = {
                "file_path": f"{uuid.uuid4().hex}.py",
                "content": invalid_content,
                "commit_message": uuid.uuid4().hex
            }
            res_invalid = self.verifier.verify_and_apply(invalid_patch)
            self.assertFalse(res_invalid)

    def test_exceptions_exist(self):
        self.assertTrue(issubclass(HypothesisGeneratorError, Exception))
        self.assertTrue(issubclass(LessonParserError, Exception))
        self.assertTrue(issubclass(PatchExecutorError, Exception))