import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
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

    def test_git_inspector_get_commit_history_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            max_count = random.randint(1, 20)
            history = self.inspector.get_commit_history(max_count)
            self.assertEqual(history, [])

    def test_git_inspector_get_commit_history_valid(self):
        commit_hash = uuid.uuid4().hex
        author_name = f"Author_{uuid.uuid4().hex[:6]}"
        commit_msg = f"Message_{uuid.uuid4().hex[:6]}"
        stdout_data = f"{commit_hash}|{author_name}|{commit_msg}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=stdout_data, stderr="")
            history = self.inspector.get_commit_history(10)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], commit_hash)
            self.assertEqual(history[0]["author"], author_name)
            self.assertEqual(history[0]["message"], commit_msg)

    def test_git_inspector_analyze_repository(self):
        commit_hash = uuid.uuid4().hex
        author_name = f"Author_{uuid.uuid4().hex[:6]}"
        commit_msg = f"Message_{uuid.uuid4().hex[:6]}"
        stdout_data = f"{commit_hash}|{author_name}|{commit_msg}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=stdout_data, stderr="")
            analysis = self.inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertIsNotNone(analysis["latest_commit"])
            self.assertEqual(analysis["latest_commit"]["hash"], commit_hash)

    def test_git_inspector_get_latest_changes(self):
        commit_hash = uuid.uuid4().hex
        author_name = f"Author_{uuid.uuid4().hex[:6]}"
        commit_msg = f"Message_{uuid.uuid4().hex[:6]}"
        history_stdout = f"{commit_hash}|{author_name}|{commit_msg}"
        diff_stdout = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=history_stdout, stderr=""),
                MagicMock(stdout=diff_stdout, stderr="")
            ]
            changes = self.inspector.get_latest_changes()
            self.assertEqual(changes, diff_stdout)

    def test_lesson_parser_extraction(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = self.parser.extract_lessons(random.randint(1, 15))
        self.assertIn("lesson_id", extracted)
        self.assertIn("content", extracted)

    def test_hypothesis_generator_prioritization(self):
        hyp_id_1 = f"hyp_{uuid.uuid4().hex[:6]}"
        hyp_id_2 = f"hyp_{uuid.uuid4().hex[:6]}"
        weight_1 = random.uniform(0.1, 0.4)
        weight_2 = random.uniform(0.5, 0.9)
        
        hypotheses = [
            {"id": hyp_id_1, "weight": weight_1, "target": f"{uuid.uuid4().hex}.py"},
            {"id": hyp_id_2, "weight": weight_2, "target": f"{uuid.uuid4().hex}.py"}
        ]
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["id"], hyp_id_2)
        self.assertEqual(prioritized[1]["id"], hyp_id_1)

    def test_patch_executor_apply_patch_failure(self):
        patch_data = {}
        result = self.executor.apply_patch(patch_data)
        self.assertFalse(result)

    def test_patch_executor_apply_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        content = f"# {uuid.uuid4().hex}"
        commit_msg = f"Commit {uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        with patch("builtins.open", create=True) as mock_open, \
             patch("os.makedirs") as mock_makedirs, \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_makedirs.assert_called_once()
            mock_open.assert_called_once()

    def test_patch_executor_rollback_patch(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(result)

    def test_patch_verifier_syntax_error(self):
        bad_content = f"print(uuid.uuid4()) \n syntax error here \n {uuid.uuid4().hex}"
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": bad_content
        }
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    def test_patch_verifier_success(self):
        good_content = f"def {uuid.uuid4().hex[:8]}(): pass"
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": good_content
        }

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            result = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(result)
            mock_apply.assert_called_once_with(patch_data)


if __name__ == "__main__":
    unittest.main()