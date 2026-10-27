import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import subprocess
import io
import random
import uuid
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

class TestPatchVerifierModuleInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(repo_path=self.repo_path)
        self.parser = LessonParser(inspector=self.inspector)
        self.generator = HypothesisGenerator(inspector=self.inspector, parser=self.parser)
        self.executor = PatchExecutor(repo_path=self.repo_path, inspector=self.inspector, parser=self.parser)
        self.verifier = PatchVerifier(repo_path=self.repo_path, inspector=self.inspector, executor=self.executor)

    @patch("subprocess.run")
    def test_git_inspector_run_git_success(self, mock_run):
        random_hash = uuid.uuid4().hex
        random_author = uuid.uuid4().hex[:8]
        random_msg = uuid.uuid4().hex
        mock_output = f"{random_hash}|{random_author}|{random_msg}\n"

        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_run.return_value = mock_result

        history = self.inspector.get_commit_history(max_count=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], random_hash)
        self.assertEqual(history[0]["author"], random_author)
        self.assertEqual(history[0]["message"], random_msg)

    @patch("subprocess.run")
    def test_git_inspector_get_file_diff(self, mock_run):
        random_hash = uuid.uuid4().hex
        random_diff = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        mock_result = MagicMock()
        mock_result.stdout = random_diff
        mock_run.return_value = mock_result

        diff = self.inspector.get_file_diff(random_hash)
        self.assertEqual(diff, random_diff)

    @patch("subprocess.run")
    def test_git_inspector_analyze_repository(self, mock_run):
        random_hash = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = f"{random_hash}|author|msg\n"
        mock_run.return_value = mock_result

        analysis = self.inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"]["hash"], random_hash)

    def test_lesson_parser_extract_lessons(self):
        lessons = self.parser.extract_lessons()
        self.assertIn("lesson_id", lessons)
        self.assertIn("content", lessons)

    def test_hypothesis_generator_prioritize(self):
        hyp1_id = uuid.uuid4().hex
        hyp2_id = uuid.uuid4().hex
        hypotheses = [
            {"id": hyp1_id, "weight": random.random()},
            {"id": hyp2_id, "weight": random.random() + 1.0}
        ]
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["id"], hyp2_id)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_patch_executor_apply_patch_success(self, mock_makedirs, mock_file, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        content = f"# {uuid.uuid4().hex}"
        commit_msg = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        result = self.executor.apply_patch(patch_data)
        self.assertTrue(result)
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(content)
        self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_patch_invalid_data(self):
        patch_data = {"file_path": "", "content": None}
        result = self.executor.apply_patch(patch_data)
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch(self, mock_run):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        result = self.executor.rollback_patch(file_path, commit_hash)
        self.assertTrue(result)
        mock_run.assert_called_once()

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        bad_content = f"syntax error here {uuid.uuid4().hex}"
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": bad_content
        }
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    @patch("skills.patch_verifier.PatchExecutor.apply_patch")
    def test_patch_verifier_verify_and_apply_success(self, mock_apply):
        mock_apply.return_value = True
        good_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": good_content
        }
        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)
        mock_apply.assert_called_once_with(patch_data)

if __name__ == "__main__":
    unittest.main()