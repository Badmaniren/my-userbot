import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import io
from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestPatchExecutorStrict(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.git_inspector = unittest.mock.MagicMock()
        self.lesson_parser = unittest.mock.MagicMock()
        self.executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def test_init_with_git_inspector_repo_path(self):
        rand_path = f"/tmp/{uuid.uuid4().hex}"
        inspector = unittest.mock.MagicMock()
        inspector.repo_path = rand_path
        executor = PatchExecutor(git_inspector=inspector)
        self.assertEqual(executor.repo_path, rand_path)

    def test_apply_patch_invalid_format_not_dict(self):
        rand_val = random.choice([uuid.uuid4().hex, random.randint(1, 100), None])
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch(rand_val)

    def test_apply_patch_missing_file_path(self):
        patch_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "content": uuid.uuid4().hex
        }
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch(patch_data)

    def test_apply_patch_missing_content(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        with self.assertRaises(PatchExecutorError):
            self.executor.apply_patch(patch_data)

    def test_apply_patch_success_relative_path(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"# {uuid.uuid4().hex}"
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }
        expected_full_path = os.path.join(self.repo_path, file_name)

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            result = self.executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_makedirs.assert_called_once_with(os.path.dirname(expected_full_path), exist_ok=True)
            mock_file.assert_called_once_with(expected_full_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_success_absolute_path(self):
        abs_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        file_content = f"# {uuid.uuid4().hex}"
        patch_data = {
            "file_path": abs_path,
            "content": file_content
        }

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            result = self.executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_makedirs.assert_called_once_with(os.path.dirname(abs_path), exist_ok=True)
            mock_file.assert_called_once_with(abs_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_io_exception(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = uuid.uuid4().hex
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }

        with patch("os.makedirs"), \
             patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(patch_data)

    def test_execute_from_lessons_no_parser(self):
        executor_no_parser = PatchExecutor(repo_path=self.repo_path)
        res = executor_no_parser.execute_from_lessons()
        self.assertEqual(res, {})

    def test_execute_from_lessons_success_and_failure(self):
        hyp_id_1 = uuid.uuid4().hex
        hyp_id_2 = uuid.uuid4().hex
        file_path_1 = f"{uuid.uuid4().hex}.py"
        file_path_2 = f"{uuid.uuid4().hex}.py"
        
        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id_1,
                "patches": [{"file_path": file_path_1, "content": uuid.uuid4().hex}]
            },
            {
                "id": hyp_id_2,
                "patches": [{"file_path": file_path_2, "content": uuid.uuid4().hex}]
            }
        ]

        with patch.object(self.executor, "apply_patch", side_effect=[True, Exception(uuid.uuid4().hex)]) as mock_apply:
            results = self.executor.execute_from_lessons()
            self.assertEqual(results, {
                hyp_id_1: True,
                hyp_id_2: False
            })
            self.assertEqual(mock_apply.call_count, 2)

    def test_rollback_patch_no_git_inspector(self):
        executor_no_git = PatchExecutor(repo_path=self.repo_path)
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        res = executor_no_git.rollback_patch(file_path, commit_hash)
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

    def test_rollback_patch_exception_raised(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        self.git_inspector.read_file_at_commit.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchExecutorError):
            self.executor.rollback_patch(file_path, commit_hash)

if __name__ == "__main__":
    unittest.main()