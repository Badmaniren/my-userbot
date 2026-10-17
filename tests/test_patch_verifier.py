import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
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

class TestPatchVerifierSuite(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.random_file = f"src/{uuid.uuid4().hex[:6]}.py"
        self.random_hash = uuid.uuid4().hex
        self.random_author = f"Author_{uuid.uuid4().hex[:4]}"
        self.random_message = f"Commit message {uuid.uuid4().hex[:6]}"
        self.random_content = f"print('{uuid.uuid4().hex}')"
        
        self.inspector = GitInspector(self.random_repo)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.random_repo, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.random_repo, self.inspector, self.executor)

    def test_git_inspector_run_git_success(self):
        expected_output = f"output_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.stdout = expected_output + "\n"
            mock_run.return_value = mock_res
            
            random_arg = uuid.uuid4().hex
            result = self.inspector._run_git([random_arg])
            self.assertEqual(result, expected_output)
            mock_run.assert_called_once()

    def test_git_inspector_get_commit_history(self):
        commit_line = f"{self.random_hash}|{self.random_author}|{self.random_message}"
        with patch.object(self.inspector, "_run_git", return_value=commit_line) as mock_run:
            count = random.randint(1, 50)
            history = self.inspector.get_commit_history(max_count=count)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], self.random_hash)
            self.assertEqual(history[0]["author"], self.random_author)
            self.assertEqual(history[0]["message"], self.random_message)
            mock_run.assert_called_once_with(["log", f"-n {count}", "--pretty=format:%H|%an|%s"])

    def test_git_inspector_get_commit_history_empty(self):
        with patch.object(self.inspector, "_run_git", return_value="") as mock_run:
            history = self.inspector.get_commit_history()
            self.assertEqual(history, [])

    def test_git_inspector_get_file_diff(self):
        diff_text = f"diff --git a/{self.random_file} b/{self.random_file}\n+{self.random_content}"
        with patch.object(self.inspector, "_run_git", return_value=diff_text) as mock_run:
            res = self.inspector.get_file_diff(self.random_hash)
            self.assertEqual(res, diff_text)
            mock_run.assert_called_once_with(["show", self.random_hash])

    def test_git_inspector_analyze_repository(self):
        commit_line = f"{self.random_hash}|{self.random_author}|{self.random_message}"
        with patch.object(self.inspector, "_run_git", return_value=commit_line):
            analysis = self.inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], self.random_hash)

    def test_git_inspector_read_file_at_commit(self):
        file_content = f"def {uuid.uuid4().hex}(): pass"
        with patch.object(self.inspector, "_run_git", return_value=file_content) as mock_run:
            res = self.inspector.read_file_at_commit(self.random_hash, self.random_file)
            self.assertEqual(res, file_content)
            mock_run.assert_called_once_with(["show", f"{self.random_hash}:{self.random_file}"])

    def test_git_inspector_aliases(self):
        with patch.object(self.inspector, "get_commit_history", return_value=[{"hash": self.random_hash}]) as mock_hist:
            res = self.inspector.get_history(5)
            self.assertEqual(res[0]["hash"], self.random_hash)
            mock_hist.assert_called_once_with(5)

        with patch.object(self.inspector, "get_commit_history", return_value=[{"hash": self.random_hash}]), \
             patch.object(self.inspector, "get_file_diff", return_value=self.random_content) as mock_diff:
            res = self.inspector.get_latest_changes()
            self.assertEqual(res, self.random_content)
            mock_diff.assert_called_once_with(self.random_hash)

    def test_lesson_parser_methods(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertIn("lesson_id", lessons[0])

        extracted = self.parser.extract_lessons(max_commits=random.randint(1, 10))
        self.assertIsInstance(extracted, dict)
        self.assertIn("content", extracted)

    def test_hypothesis_generator_methods(self):
        hg = HypothesisGenerator(self.inspector, self.parser)
        hyps = hg.generate_hypotheses()
        self.assertIsInstance(hyps, list)
        
        hyp_list = [
            {"id": uuid.uuid4().hex, "weight": random.random()},
            {"id": uuid.uuid4().hex, "weight": random.random() + 1.0}
        ]
        prioritized = hg.prioritize_hypotheses(hyp_list)
        self.assertGreaterEqual(prioritized[0]["weight"], prioritized[1]["weight"])

    def test_patch_executor_apply_patch_success(self):
        patch_data = {
            "file_path": self.random_file,
            "content": self.random_content,
            "commit_message": self.random_message
        }
        with patch("os.makedirs") as mock_mkdirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_subproc:
            
            res = self.executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_mkdirs.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(mock_subproc.call_count, 2)

    def test_patch_executor_apply_patch_missing_fields(self):
        bad_patch = {"content": self.random_content}
        res = self.executor.apply_patch(bad_patch)
        self.assertFalse(res)

    def test_patch_executor_apply_patch_exception(self):
        patch_data = {
            "file_path": self.random_file,
            "content": self.random_content
        }
        with patch("os.makedirs", side_effect=Exception(uuid.uuid4().hex)):
            res = self.executor.apply_patch(patch_data)
            self.assertFalse(res)

    def test_patch_executor_rollback_patch(self):
        with patch("subprocess.run") as mock_subproc:
            res = self.executor.rollback_patch(self.random_file, self.random_hash)
            self.assertTrue(res)
            mock_subproc.assert_called_once()

    def test_patch_executor_rollback_patch_exception(self):
        with patch("subprocess.run", side_effect=Exception(uuid.uuid4().hex)):
            res = self.executor.rollback_patch(self.random_file, self.random_hash)
            self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        error_content = f"code {uuid.uuid4().hex} syntax error here"
        patch_data = {
            "file_path": self.random_file,
            "content": error_content
        }
        with patch.object(self.executor, "apply_patch") as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertFalse(res)
            mock_apply.assert_not_called()

    def test_patch_verifier_verify_and_apply_success(self):
        patch_data = {
            "file_path": self.random_file,
            "content": self.random_content
        }
        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)

    def test_exceptions_instantiation(self):
        err_msg = uuid.uuid4().hex
        ex1 = HypothesisGeneratorError(err_msg)
        ex2 = LessonParserError(err_msg)
        ex3 = PatchExecutorError(err_msg)
        
        self.assertIsInstance(ex1, Exception)
        self.assertIsInstance(ex2, Exception)
        self.assertIsInstance(ex3, Exception)

if __name__ == "__main__":
    unittest.main()