import unittest
import os
import uuid
import random
import subprocess
from unittest.mock import patch, MagicMock
from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier,
    PatchVerifierError,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)

class TestPatchVerifierModule(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector_mock = MagicMock(spec=GitInspector)
        self.parser_mock = MagicMock(spec=LessonParser)
        self.executor_mock = MagicMock(spec=PatchExecutor)
        self.verifier = PatchVerifier(self.repo_path, self.inspector_mock, self.executor_mock)

    def test_git_inspector_run_git_success(self):
        inspector = GitInspector(self.repo_path)
        random_commit = uuid.uuid4().hex
        random_author = uuid.uuid4().hex
        random_message = uuid.uuid4().hex
        git_output = f"{random_commit}|{random_author}|{random_message}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            mock_run.return_value.stderr = ""
            
            history = inspector.get_commit_history(max_count=1)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], random_commit)
            self.assertEqual(history[0]["author"], random_author)
            self.assertEqual(history[0]["message"], random_message)

    def test_git_inspector_empty_history(self):
        inspector = GitInspector(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""

            history = inspector.get_commit_history(max_count=random.randint(1, 10))
            self.assertEqual(history, [])

    def test_git_inspector_get_file_diff(self):
        inspector = GitInspector(self.repo_path)
        commit_hash = uuid.uuid4().hex
        expected_diff = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = expected_diff
            res = inspector.get_file_diff(commit_hash)
            self.assertEqual(res, expected_diff)

    def test_git_inspector_analyze_repository(self):
        inspector = GitInspector(self.repo_path)
        commit_hash = uuid.uuid4().hex
        author = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        git_output = f"{commit_hash}|{author}|{msg}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = git_output
            analysis = inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], commit_hash)

    def test_git_inspector_read_file_at_commit(self):
        inspector = GitInspector(self.repo_path)
        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        file_content = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = file_content
            res = inspector.read_file_at_commit(commit_hash, file_path)
            self.assertEqual(res, file_content)

    def test_git_inspector_aliases(self):
        inspector = GitInspector(self.repo_path)
        with patch.object(inspector, "get_commit_history") as mock_history:
            inspector.get_history(5)
            mock_history.assert_called_once_with(5)

        with patch.object(inspector, "get_commit_history") as mock_history, \
             patch.object(inspector, "get_file_diff") as mock_diff:
            commit_hash = uuid.uuid4().hex
            mock_history.return_value = [{"hash": commit_hash}]
            mock_diff.return_value = uuid.uuid4().hex

            res = inspector.get_latest_changes()
            mock_diff.assert_called_once_with(commit_hash)

    def test_lesson_parser_methods(self):
        parser = LessonParser(self.inspector_mock)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        extracted = parser.extract_lessons(max_commits=random.randint(1, 15))
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_methods(self):
        generator = HypothesisGenerator(self.inspector_mock, self.parser_mock)
        hyps = generator.generate_hypotheses(max_commits=random.randint(1, 5))
        self.assertIsInstance(hyps, list)

        prioritized = generator.prioritize_hypotheses([
            {"id": uuid.uuid4().hex, "weight": random.random()},
            {"id": uuid.uuid4().hex, "weight": random.random() + 1.0}
        ])
        self.assertTrue(prioritized[0]["weight"] >= prioritized[1]["weight"])

    def test_patch_executor_apply_patch_success(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, self.parser_mock)
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        commit_message = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_message
        }

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run:
            
            res = executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_file.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)

    def test_patch_executor_apply_patch_invalid_data(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, self.parser_mock)
        patch_data = {"content": uuid.uuid4().hex}
        res = executor.apply_patch(patch_data)
        self.assertFalse(res)

    def test_patch_executor_rollback_and_execute_lessons(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, self.parser_mock)
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            res_rollback = executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(res_rollback)

        res_exec = executor.execute_from_lessons()
        self.assertIsInstance(res_exec, dict)
        self.assertIn("status", res_exec)

    def test_patch_verifier_verify_and_apply_success(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": f"print('{uuid.uuid4().hex}')"
        }
        self.executor_mock.apply_patch.return_value = True

        res = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(res)
        self.executor_mock.apply_patch.assert_called_once()

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": "syntax error here: " + uuid.uuid4().hex
        }

        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)
        self.executor_mock.apply_patch.assert_not_called()

    def test_patch_verifier_positional_arguments(self):
        file_name = "test_file.py"
        code_fragment = "x = 10\ny = 20\n"
        self.assertTrue(self.verifier.verify(file_name, code_fragment))

        invalid_fragment = "def invalid_func(:"
        self.assertFalse(self.verifier.verify(file_name, invalid_fragment))

    def test_patch_verifier_default_init(self):
        verifier = PatchVerifier(self.repo_path)
        self.assertIsNotNone(verifier.inspector)
        self.assertIsNotNone(verifier.executor)

    def test_exceptions_exist(self):
        self.assertTrue(issubclass(PatchVerifierError, Exception))
        self.assertTrue(issubclass(HypothesisGeneratorError, Exception))
        self.assertTrue(issubclass(LessonParserError, Exception))
        self.assertTrue(issubclass(PatchExecutorError, Exception))
