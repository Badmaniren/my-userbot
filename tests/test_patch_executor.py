import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import tempfile
import shutil

from skills.patch_executor import PatchExecutor, PatchExecutorError


class TestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.git_inspector = MagicMock()
        self.lesson_parser = MagicMock()
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_with_git_inspector_fallback(self):
        rand_path = os.path.join(self.test_dir, uuid.uuid4().hex)
        mock_inspector = MagicMock()
        mock_inspector.repo_path = rand_path

        executor = PatchExecutor(git_inspector=mock_inspector)
        self.assertEqual(executor.repo_path, rand_path)
        self.assertEqual(executor.git_inspector, mock_inspector)

    def test_init_default_repo_path(self):
        executor = PatchExecutor()
        self.assertEqual(executor.repo_path, ".")

    def test_apply_patch_invalid_format_raises_error(self):
        invalid_data = [
            uuid.uuid4().hex,
            {uuid.uuid4().hex: uuid.uuid4().hex},
            {"file_path": uuid.uuid4().hex},
            {"content": uuid.uuid4().hex}
        ]
        for data in invalid_data:
            with self.subTest(data=data):
                with self.assertRaises(PatchExecutorError):
                    self.patch_executor.apply_patch(data)

    def test_apply_patch_success_relative_path(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"# {uuid.uuid4().hex}\ndef {uuid.uuid4().hex}(): pass"
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }

        result = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.repo_path, file_name)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content)

    def test_apply_patch_success_absolute_path(self):
        sub_dir = tempfile.mkdtemp(dir=self.test_dir)
        file_name = os.path.join(sub_dir, f"{uuid.uuid4().hex}.txt")
        file_content = uuid.uuid4().hex
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }

        result = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(result)

        self.assertTrue(os.path.exists(file_name))
        with open(file_name, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content)

    def test_apply_patch_io_error_raises_patch_executor_error(self):
        file_name = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        patch_data = {
            "file_path": file_name,
            "content": uuid.uuid4().hex
        }

        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(PatchExecutorError):
                self.patch_executor.apply_patch(patch_data)

    def test_execute_from_lessons_no_parser(self):
        executor = PatchExecutor(repo_path=self.repo_path)
        res = executor.execute_from_lessons()
        self.assertEqual(res, {})

    def test_execute_from_lessons_success(self):
        hyp_id_1 = uuid.uuid4().hex
        hyp_id_2 = uuid.uuid4().hex
        file_path_1 = f"{uuid.uuid4().hex}.py"
        file_path_2 = f"{uuid.uuid4().hex}.py"
        content_1 = uuid.uuid4().hex
        content_2 = uuid.uuid4().hex

        mock_lessons = [
            {
                "id": hyp_id_1,
                "patches": [{"file_path": file_path_1, "content": content_1}]
            },
            {
                "id": hyp_id_2,
                "patches": [{"file_path": file_path_2, "content": content_2}]
            }
        ]
        self.lesson_parser.parse_lessons.return_value = mock_lessons

        results = self.patch_executor.execute_from_lessons()

        self.assertEqual(results, {hyp_id_1: True, hyp_id_2: True})
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, file_path_1)))
        self.assertTrue(os.path.exists(os.path.join(self.repo_path, file_path_2)))

    def test_execute_from_lessons_partial_failure(self):
        hyp_id_good = uuid.uuid4().hex
        hyp_id_bad = uuid.uuid4().hex
        file_path_good = f"{uuid.uuid4().hex}.py"
        file_path_bad = f"{uuid.uuid4().hex}.py"

        mock_lessons = [
            {
                "id": hyp_id_good,
                "patches": [{"file_path": file_path_good, "content": uuid.uuid4().hex}]
            },
            {
                "id": hyp_id_bad,
                "patches": [{"file_path": file_path_bad, "content": uuid.uuid4().hex}, {"file_path": "", "content": ""}]
            }
        ]
        self.lesson_parser.parse_lessons.return_value = mock_lessons

        results = self.patch_executor.execute_from_lessons()

        self.assertEqual(results[hyp_id_good], True)
        self.assertEqual(results[hyp_id_bad], False)

    def test_rollback_patch_no_git_inspector(self):
        executor = PatchExecutor(repo_path=self.repo_path)
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        res = executor.rollback_patch(file_path, commit_hash)
        self.assertFalse(res)

    def test_rollback_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        original_content = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.return_value = original_content

        res = self.patch_executor.rollback_patch(file_path, commit_hash)

        self.assertTrue(res)
        self.git_inspector.read_file_at_commit.assert_called_once_with(commit_hash, file_path)

        full_path = os.path.join(self.repo_path, file_path)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), original_content)

    def test_rollback_patch_exception_raises_patch_executor_error(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchExecutorError):
            self.patch_executor.rollback_patch(file_path, commit_hash)