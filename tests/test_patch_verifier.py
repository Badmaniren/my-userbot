import unittest
from unittest.mock import patch, mock_open
import subprocess
import os
import random
import uuid
import io

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
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def test_git_inspector_run_git_success(self):
        random_hash = uuid.uuid4().hex
        random_stdout = f"{random_hash}|Author|Commit message {uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = random_stdout
            mock_run.return_value.stderr = ""
            result = self.inspector._run_git(["log"])
            self.assertEqual(result, random_stdout.strip())
            mock_run.assert_called_once()

    def test_git_inspector_get_commit_history_random(self):
        h1 = uuid.uuid4().hex
        a1 = uuid.uuid4().hex
        m1 = uuid.uuid4().hex
        mock_output = f"{h1}|{a1}|{m1}"

        with patch.object(self.inspector, "_run_git", return_value=mock_output) as mock_run:
            history = self.inspector.get_commit_history(max_count=1)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], h1)
            self.assertEqual(history[0]["author"], a1)
            self.assertEqual(history[0]["message"], m1)
            mock_run.assert_called_once()

    def test_git_inspector_analyze_repository(self):
        h1 = uuid.uuid4().hex
        a1 = uuid.uuid4().hex
        m1 = uuid.uuid4().hex
        mock_output = f"{h1}|{a1}|{m1}"

        with patch.object(self.inspector, "_run_git", return_value=mock_output):
            analysis = self.inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], h1)

    def test_git_inspector_read_file_at_commit(self):
        commit = uuid.uuid4().hex
        filename = f"{uuid.uuid4().hex}.py"
        expected_content = f"content_{uuid.uuid4().hex}"

        with patch.object(self.inspector, "_run_git", return_value=expected_content) as mock_run:
            content = self.inspector.read_file_at_commit(commit, filename)
            self.assertEqual(content, expected_content)
            mock_run.assert_called_with(["show", f"{commit}:{filename}"])

    def test_git_inspector_get_latest_changes(self):
        h1 = uuid.uuid4().hex
        diff_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        with patch.object(self.inspector, "get_commit_history", return_value=[{"hash": h1, "author": "dev", "message": "msg"}]):
            with patch.object(self.inspector, "get_file_diff", return_value=diff_text) as mock_diff:
                res = self.inspector.get_latest_changes()
                self.assertEqual(res, diff_text)
                mock_diff.assert_called_with(h1)

    def test_lesson_parser_extraction(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = self.parser.extract_lessons()
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_prioritize(self):
        h_id_1 = uuid.uuid4().hex
        h_id_2 = uuid.uuid4().hex
        weight_low = random.uniform(0.1, 0.4)
        weight_high = random.uniform(0.5, 0.9)

        hypotheses = [
            {"id": h_id_1, "weight": weight_low},
            {"id": h_id_2, "weight": weight_high}
        ]
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["id"], h_id_2)
        self.assertEqual(prioritized[1]["id"], h_id_1)

    def test_patch_executor_apply_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        msg = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": msg
        }

        m_open = mock_open()
        with patch("builtins.open", m_open), \
             patch("os.makedirs") as mock_makedirs, \
             patch("subprocess.run") as mock_subproc:
            
            success = self.executor.apply_patch(patch_data)
            self.assertTrue(success)
            mock_makedirs.assert_called_once()
            m_open.assert_called_once()
            self.assertEqual(mock_subproc.call_count, 2)

    def test_patch_executor_apply_patch_missing_data(self):
        patch_data = {"file_path": f"{uuid.uuid4().hex}.py"} # нет content
        success = self.executor.apply_patch(patch_data)
        self.assertFalse(success)

    def test_patch_executor_rollback_patch(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_subproc:
            res = self.executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(res)
            mock_subproc.assert_called_once()

    def test_patch_executor_rollback_patch_exception(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run", side_effect=Exception("Git error")):
            res = self.executor.rollback_patch(file_path, commit_hash)
            self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIn("executed_lessons", res)
        self.assertEqual(res["status"], "success")

    def test_patch_verifier_verify_and_apply_success(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": f"x = {random.randint(1, 100)}"
        }
        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": f"syntax error here {uuid.uuid4().hex}"
        }
        with patch.object(self.executor, "apply_patch") as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertFalse(res)
            mock_apply.assert_not_called()