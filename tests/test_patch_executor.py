import os
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/{uuid.uuid4().hex}"
        self.git_inspector_mock = MagicMock()
        self.git_inspector_mock.repo_path = self.random_repo
        self.lesson_parser_mock = MagicMock()
        
        self.executor = PatchExecutor(
            repo_path=self.random_repo,
            git_inspector=self.git_inspector_mock,
            lesson_parser=self.lesson_parser_mock
        )

    def test_init_resolves_repo_path_from_inspector(self):
        rand_path = f"/var/tmp/{uuid.uuid4().hex}"
        inspector = MagicMock()
        inspector.repo_path = rand_path
        
        executor = PatchExecutor(git_inspector=inspector)
        self.assertEqual(executor.repo_path, rand_path)

    def test_init_defaults_to_current_directory(self):
        executor = PatchExecutor()
        self.assertEqual(executor.repo_path, ".")

    def test_apply_patch_invalid_data_raises_error(self):
        invalid_inputs = [
            random.choice([None, "string", 123, []]),
            {uuid.uuid4().hex: uuid.uuid4().hex},
            {"file_path": uuid.uuid4().hex}
        ]
        for bad_data in invalid_inputs:
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(bad_data)

    def test_apply_patch_success_relative_path(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"# {uuid.uuid4().hex}\nprint('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }

        full_expected_path = os.path.join(self.random_repo, file_name)

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            
            result = self.executor.apply_patch(patch_data)
            
            self.assertTrue(result)
            mock_makedirs.assert_called_once_with(os.path.dirname(full_expected_path), exist_ok=True)
            mock_file.assert_called_once_with(full_expected_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_success_absolute_path(self):
        abs_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        file_content = uuid.uuid4().hex
        patch_data = {
            "file_path": abs_path,
            "content": file_content
        }

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            
            result = self.executor.apply_patch(patch_data)
            
            self.assertTrue(result)
            mock_makedirs.assert_called_once_with(os.path.dirname(abs_path), exist_ok=True)
            mock_file.assert_called_once_with(abs_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_io_error_raises_patch_executor_error(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.txt",
            "content": uuid.uuid4().hex
        }

        with patch("os.makedirs"), \
             patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(patch_data)

    def test_execute_from_lessons_no_parser(self):
        executor = PatchExecutor(repo_path=self.random_repo)
        results = executor.execute_from_lessons()
        self.assertEqual(results, {})

    def test_execute_from_lessons_success_and_failure(self):
        hyp_id_1 = uuid.uuid4().hex
        hyp_id_2 = uuid.uuid4().hex
        
        path_1 = f"{uuid.uuid4().hex}.py"
        path_2 = f"{uuid.uuid4().hex}.py"
        
        content_1 = uuid.uuid4().hex
        content_2 = uuid.uuid4().hex

        hypotheses = [
            {
                "id": hyp_id_1,
                "patches": [{"file_path": path_1, "content": content_1}]
            },
            {
                "id": hyp_id_2,
                "patches": [{"file_path": path_2, "content": content_2}]
            }
        ]

        self.lesson_parser_mock.parse_lessons.return_value = hypotheses

        with patch.object(self.executor, "apply_patch") as mock_apply:
            mock_apply.side_effect = [True, PatchExecutorError(uuid.uuid4().hex)]
            
            results = self.executor.execute_from_lessons()
            
            self.assertEqual(results, {
                hyp_id_1: True,
                hyp_id_2: False
            })

    def test_rollback_patch_no_git_inspector(self):
        executor = PatchExecutor(repo_path=self.random_repo)
        res = executor.rollback_patch(uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(res)

    def test_rollback_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        original_content = uuid.uuid4().hex

        self.git_inspector_mock.read_file_at_commit.return_value = original_content

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            result = self.executor.rollback_patch(file_path, commit_hash)
            
            self.assertTrue(result)
            self.git_inspector_mock.read_file_at_commit.assert_called_once_with(commit_hash, file_path)
            mock_apply.assert_called_once_with({
                "file_path": file_path,
                "content": original_content,
                "mode": "overwrite"
            })

    def test_rollback_patch_failure_raises_error(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        self.git_inspector_mock.read_file_at_commit.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchExecutorError):
            self.executor.rollback_patch(file_path, commit_hash)

if __name__ == "__main__":
    unittest.main()