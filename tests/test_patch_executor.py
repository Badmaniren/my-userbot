import unittest
from unittest.mock import patch, MagicMock, mock_open
import io
import random
import uuid
import string

from skills.patch_executor import PatchExecutor, PatchExecutorError


class TestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.git_inspector_mock = MagicMock()
        self.lesson_parser_mock = MagicMock()
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector_mock,
            lesson_parser=self.lesson_parser_mock
        )

    def test_init_sets_attributes(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        gi = MagicMock()
        lp = MagicMock()
        executor = PatchExecutor(repo_path=random_path, git_inspector=gi, lesson_parser=lp)
        self.assertEqual(executor.repo_path, random_path)
        self.assertEqual(executor.git_inspector, gi)
        self.assertEqual(executor.lesson_parser, lp)

    def test_apply_patch_success(self):
        target_file = f"{uuid.uuid4().hex}.py"
        unique_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": target_file,
            "content": unique_content,
            "mode": "overwrite"
        }

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=True):
                result = self.patch_executor.apply_patch(patch_data)

        self.assertTrue(result)
        mock_file.assert_called_once_with(f"{self.repo_path}/{target_file}", "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(unique_content)

    def test_apply_patch_raises_error_on_invalid_data(self):
        random_key = uuid.uuid4().hex
        malformed_patch = {random_key: random.randint(100, 999)}

        with self.assertRaises(PatchExecutorError):
            self.patch_executor.apply_patch(malformed_patch)

    def test_execute_hypothesis_workflow(self):
        hypothesis_id = uuid.uuid4().hex
        target_file = f"{uuid.uuid4().hex}.py"
        code_snippet = f"def foo_{uuid.uuid4().hex}(): pass"

        hypothesis = {
            "id": hypothesis_id,
            "patches": [
                {
                    "file_path": target_file,
                    "content": code_snippet,
                    "mode": "write"
                }
            ]
        }

        self.lesson_parser_mock.parse_lessons.return_value = [hypothesis]

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch("os.makedirs") as mock_makedirs:
                executed_results = self.patch_executor.execute_from_lessons()

        self.assertIn(hypothesis_id, executed_results)
        self.assertTrue(executed_results[hypothesis_id])
        mock_makedirs.assert_called()
        mock_file().write.assert_called_with(code_snippet)

    def test_verify_patch_execution_failure(self):
        target_file = f"{uuid.uuid4().hex}.py"
        random_error = uuid.uuid4().hex
        patch_data = {
            "file_path": target_file,
            "content": uuid.uuid4().hex
        }

        with patch("builtins.open", side_effect=IOError(random_error)):
            with self.assertRaises(PatchExecutorError) as ctx:
                self.patch_executor.apply_patch(patch_data)

        self.assertIn(random_error, str(ctx.exception))

    def test_rollback_patch(self):
        backup_path = f"/tmp/{uuid.uuid4().hex}.bak"
        target_file = f"{uuid.uuid4().hex}.py"
        random_hash = uuid.uuid4().hex

        self.git_inspector_mock.read_file_at_commit.return_value = f"original_{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=True):
            mock_file = mock_open()
            with patch("builtins.open", mock_file):
                res = self.patch_executor.rollback_patch(target_file, random_hash)

        self.assertTrue(res)
        self.git_inspector_mock.read_file_at_commit.assert_called_once_with(random_hash, target_file)


if __name__ == "__main__":
    unittest.main()