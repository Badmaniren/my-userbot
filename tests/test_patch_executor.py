import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import tempfile
import io
from skills.patch_executor import PatchExecutor, PatchExecutorError


class TestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.git_inspector = MagicMock()
        self.lesson_parser = MagicMock()
        self.executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_init_with_git_inspector_repo_path(self):
        random_path = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        mock_inspector = MagicMock()
        mock_inspector.repo_path = random_path

        executor = PatchExecutor(git_inspector=mock_inspector)
        self.assertEqual(executor.repo_path, random_path)

    def test_apply_patch_success(self):
        filename = f"{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": filename,
            "content": content
        }

        result = self.executor.apply_patch(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.repo_path, filename)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, content)

    def test_apply_patch_absolute_path(self):
        filename = f"{uuid.uuid4().hex}.txt"
        abs_path = os.path.join(self.repo_path, filename)
        content = uuid.uuid4().hex
        patch_data = {
            "file_path": abs_path,
            "content": content
        }

        result = self.executor.apply_patch(patch_data)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(abs_path))

    def test_apply_patch_invalid_format(self):
        invalid_data = [
            uuid.uuid4().hex,
            {"file_path": uuid.uuid4().hex},
            {"content": uuid.uuid4().hex},
            "not_a_dict"
        ]
        for data in invalid_data:
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(data)

    def test_apply_patch_io_error(self):
        filename = f"{uuid.uuid4().hex}.py"
        patch_data = {
            "file_path": filename,
            "content": uuid.uuid4().hex
        }
        full_path = os.path.join(self.repo_path, filename)

        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(patch_data)

    def test_execute_from_lessons_success(self):
        hyp_id = uuid.uuid4().hex
        filename = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        
        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id,
                "patches": [
                    {
                        "file_path": filename,
                        "content": content
                    }
                ]
            }
        ]

        results = self.executor.execute_from_lessons()
        self.assertIn(hyp_id, results)
        self.assertTrue(results[hyp_id])

        full_path = os.path.join(self.repo_path, filename)
        self.assertTrue(os.path.exists(full_path))

    def test_execute_from_lessons_failure_in_patch(self):
        hyp_id = uuid.uuid4().hex
        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id,
                "patches": [
                    {
                        "file_path": 12345,  # Invalid format to trigger error
                        "content": uuid.uuid4().hex
                    }
                ]
            }
        ]

        results = self.executor.execute_from_lessons()
        self.assertIn(hyp_id, results)
        self.assertFalse(results[hyp_id])

    def test_execute_from_lessons_no_parser(self):
        executor = PatchExecutor(repo_path=self.repo_path, lesson_parser=None)
        results = executor.execute_from_lessons()
        self.assertEqual(results, {})

    def test_rollback_patch_restore_original(self):
        filename = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        original_content = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.return_value = original_content

        result = self.executor.rollback_patch(filename, commit_hash)
        self.assertTrue(result)

        self.git_inspector.read_file_at_commit.assert_called_once_with(commit_hash, filename)

        full_path = os.path.join(self.repo_path, filename)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, original_content)

    def test_rollback_patch_file_did_not_exist_initially(self):
        filename = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        full_path = os.path.join(self.repo_path, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        self.assertTrue(os.path.exists(full_path))

        self.git_inspector.read_file_at_commit.return_value = None

        result = self.executor.rollback_patch(filename, commit_hash)
        self.assertTrue(result)
        self.assertFalse(os.path.exists(full_path))

    def test_rollback_patch_no_git_inspector(self):
        executor = PatchExecutor(repo_path=self.repo_path, git_inspector=None)
        result = executor.rollback_patch(uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(result)

    def test_rollback_patch_inspector_exception(self):
        filename = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        self.git_inspector.read_file_at_commit.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchExecutorError):
            self.executor.rollback_patch(filename, commit_hash)


if __name__ == "__main__":
    unittest.main()