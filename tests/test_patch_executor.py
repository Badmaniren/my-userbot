import unittest
from unittest.mock import MagicMock, patch, mock_open
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

    def test_init_defaults_and_fallback(self):
        rand_path = f"/repo/{uuid.uuid4().hex}"
        mock_inspector = MagicMock()
        mock_inspector.repo_path = rand_path
        
        exec_fallback = PatchExecutor(git_inspector=mock_inspector)
        self.assertEqual(exec_fallback.repo_path, rand_path)
        
        exec_default = PatchExecutor()
        self.assertEqual(exec_default.repo_path, ".")

    def test_apply_patch_success(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": file_name,
            "content": file_content
        }

        mock_file = mock_open()
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file):
            result = self.executor.apply_patch(patch_data)
            
        self.assertTrue(result)
        expected_full_path = os.path.join(self.repo_path, file_name)
        mock_makedirs.assert_called_once_with(os.path.dirname(expected_full_path), exist_ok=True)
        mock_file.assert_called_once_with(expected_full_path, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_absolute_path(self):
        abs_file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        file_content = uuid.uuid4().hex
        patch_data = {
            "file_path": abs_file_path,
            "content": file_content
        }

        mock_file = mock_open()
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file):
            result = self.executor.apply_patch(patch_data)
            
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with(os.path.dirname(abs_file_path), exist_ok=True)
        mock_file.assert_called_once_with(abs_file_path, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(file_content)

    def test_apply_patch_invalid_format_raises(self):
        invalid_inputs = [
            uuid.uuid4().hex,
            {"file_path": uuid.uuid4().hex},
            {"content": uuid.uuid4().hex},
            {}
        ]
        for invalid_data in invalid_inputs:
            with self.subTest(invalid_data=invalid_data):
                with self.assertRaises(PatchExecutorError):
                    self.executor.apply_patch(invalid_data)

    def test_apply_patch_io_error_raises(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": uuid.uuid4().hex
        }
        with patch("os.makedirs"), \
             patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(PatchExecutorError):
                self.executor.apply_patch(patch_data)

    def test_execute_from_lessons_no_parser(self):
        exec_no_parser = PatchExecutor(repo_path=self.repo_path)
        res = exec_no_parser.execute_from_lessons()
        self.assertEqual(res, {})

    def test_execute_from_lessons_success(self):
        hyp_id_1 = uuid.uuid4().hex
        hyp_id_2 = uuid.uuid4().hex
        file_path_1 = f"{uuid.uuid4().hex}.py"
        file_path_2 = f"{uuid.uuid4().hex}.py"
        content_1 = uuid.uuid4().hex
        content_2 = uuid.uuid4().hex

        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id_1,
                "patches": [{"file_path": file_path_1, "content": content_1}]
            },
            {
                "id": hyp_id_2,
                "patches": [{"file_path": file_path_2, "content": content_2}]
            }
        ]

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            results = self.executor.execute_from_lessons()

        self.assertEqual(results, {hyp_id_1: True, hyp_id_2: True})
        self.assertEqual(mock_apply.call_count, 2)

    def test_execute_from_lessons_patch_failure_sets_false(self):
        hyp_id = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex

        self.lesson_parser.parse_lessons.return_value = [
            {
                "id": hyp_id,
                "patches": [{"file_path": file_path, "content": content}]
            }
        ]

        with patch.object(self.executor, "apply_patch", side_effect=PatchExecutorError(uuid.uuid4().hex)) as mock_apply:
            results = self.executor.execute_from_lessons()

        self.assertEqual(results, {hyp_id: False})
        mock_apply.assert_called_once()

    def test_rollback_patch_no_inspector(self):
        exec_no_insp = PatchExecutor(repo_path=self.repo_path)
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        res = exec_no_insp.rollback_patch(file_path, commit_hash)
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

    def test_rollback_patch_inspector_error_raises(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex

        self.git_inspector.read_file_at_commit.side_effect = Exception(err_msg)

        with self.assertRaises(PatchExecutorError) as ctx:
            self.executor.rollback_patch(file_path, commit_hash)
        
        self.assertIn(err_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()