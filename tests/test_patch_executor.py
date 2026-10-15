import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import io

from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.git_inspector = MagicMock()
        self.lesson_parser = MagicMock()
        self.executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def test_init_with_git_inspector_repo_path(self):
        rand_path = f"/tmp/{uuid.uuid4().hex}"
        inspector = MagicMock()
        inspector.repo_path = rand_path

        executor = PatchExecutor(git_inspector=inspector)
        self.assertEqual(executor.repo_path, rand_path)

    def test_apply_patch_invalid_format(self):
        rand_key = uuid.uuid4().hex
        invalid_data = {rand_key: uuid.uuid4().hex}
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch(invalid_data)

    def test_apply_patch_invalid_types(self):
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch("not_a_dict")
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch({"file_path": 123, "content": "valid"})
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch({"file_path": "valid", "content": None})

    def test_apply_patch_success(self):
        file_path = f"dir_{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": file_path,
            "content": content
        }

        mock_file = unittest.mock.mock_open()
        with patch("builtins.open", mock_file):
            with patch("os.makedirs") as mock_makedirs:
                with patch("os.replace") as mock_replace:
                    result = self.executor.apply_patch(patch_data)

                    self.assertTrue(result)
                    mock_makedirs.assert_called_once()
                    mock_file.assert_called_once()
                    mock_file.return_value.write.assert_called_once_with(content)
                    mock_replace.assert_called_once()

    def test_apply_patch_io_error(self):
        file_path = f"{uuid.uuid4().hex}.txt"
        content = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content
        }

        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with patch("os.makedirs"):
                with self.assertRaises(PatchExecutorError):
                    self.executor.apply_patch(patch_data)

    def test_execute_from_lessons_no_parser(self):
        executor_no_parser = PatchExecutor(repo_path=self.repo_path)
        res = executor_no_parser.execute_from_lessons()
        self.assertEqual(res, {})

    def test_execute_from_lessons_success(self):
        hyp_id = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        
        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id,
                "patches": [
                    {
                        "file_path": file_path,
                        "content": content
                    }
                ]
            }
        ]

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            results = self.executor.execute_from_lessons()
            self.assertIn(hyp_id, results)
            self.assertTrue(results[hyp_id])
            mock_apply.assert_called_once()

    def test_execute_from_lessons_failure(self):
        hyp_id = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex

        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id,
                "patches": [
                    {
                        "file_path": file_path,
                        "content": content
                    }
                ]
            }
        ]

        with patch.object(self.executor, "apply_patch", side_effect=PatchExecutorError(uuid.uuid4().hex)) as mock_apply:
            results = self.executor.execute_from_lessons()
            self.assertIn(hyp_id, results)
            self.assertFalse(results[hyp_id])
            mock_apply.assert_called_once()

    def test_rollback_patch_no_inspector(self):
        executor_no_insp = PatchExecutor(repo_path=self.repo_path)
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        res = executor_no_insp.rollback_patch(file_path, commit_hash)
        self.assertFalse(res)

    def test_rollback_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        original_content = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.return_value = original_content

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            res = self.executor.rollback_patch(file_path, commit_hash)

            self.assertTrue(res)
            self.git_inspector.read_file_at_commit.assert_called_once_with(commit_hash, file_path)
            mock_apply.assert_called_once_with({
                "file_path": file_path,
                "content": original_content,
                "mode": "overwrite"
            })

    def test_rollback_patch_exception(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchExecutorError):
            self.executor.rollback_patch(file_path, commit_hash)

if __name__ == "__main__":
    unittest.main()