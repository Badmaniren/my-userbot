import unittest
from unittest.mock import patch
import os
import shutil
import tempfile
import uuid
import random
import io
import ast

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = self.temp_dir
        self.applier = PatchApplier(self.repo_path)
        self.file_name = f"{uuid.uuid4().hex}.py"
        self.target_file_path = os.path.join(self.temp_dir, self.file_name)

        self.random_content = f"x = {random.randint(1, 100)}\n"
        with open(self.target_file_path, 'w', encoding='utf-8') as f:
            f.write(self.random_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_patch_syntax_success(self):
        valid_code = f"def func_{uuid.uuid4().hex[:6]}():\n    return {random.randint(100, 999)}"
        result = self.applier.validate_patch_syntax(valid_code)
        self.assertTrue(result)

    def test_validate_patch_syntax_failure(self):
        invalid_code = f"def {uuid.uuid4().hex[:6]}(:\n    pass"
        with self.assertRaises(PatchApplierError):
            self.applier.validate_patch_syntax(invalid_code)

    def test_apply_patch_direct_replacement(self):
        patch_text = f"y = {random.randint(1000, 9999)}\n"
        result = self.applier.apply_patch(self.target_file_path, patch_text)
        self.assertTrue(result)

        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, patch_text)

    def test_apply_patch_unified_diff_style(self):
        unique_str = f"val_{uuid.uuid4().hex[:6]}"
        patch_text = f"--- a/{self.file_name}\n+++ b/{self.file_name}\n@@ -1,1 +1,2@@\n+{unique_str}"

        result = self.applier.apply_patch(self.target_file_path, patch_text)
        self.assertTrue(result)

        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(unique_str, content)

    def test_apply_patch_file_not_found(self):
        non_existent = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.py")
        patch_text = f"a = {random.randint(1, 50)}"
        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(non_existent, patch_text)

    def test_apply_patch_binary_rejection(self):
        binary_file = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xff\xff\xff')

        patch_text = f"content = {random.randint(1, 100)}"
        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(binary_file, patch_text)

    def test_apply_patch_with_backup(self):
        patch_text = f"z = {random.randint(500, 600)}"
        result = self.applier.apply_patch_with_backup(self.target_file_path, patch_text)
        self.assertTrue(result)

        backups = [f for f in os.listdir(self.temp_dir) if '.bak' in f]
        self.assertTrue(len(backups) > 0)

        backup_file_path = os.path.join(self.temp_dir, backups[0])
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        self.assertEqual(backup_content, self.random_content)

    def test_apply_patch_directory_target(self):
        sub_dir = os.path.join(self.temp_dir, f"dir_{uuid.uuid4().hex[:6]}")
        os.makedirs(sub_dir)
        sub_file = os.path.join(sub_dir, f"{uuid.uuid4().hex}.py")
        orig_sub_content = f"sub_var = {random.randint(1, 10)}"
        with open(sub_file, 'w', encoding='utf-8') as f:
            f.write(orig_sub_content)

        patch_text = f"--- a/dummy.py\n+++ b/{os.path.basename(sub_file)}\n+{f'new_{uuid.uuid4().hex[:6]}'}"
        result = self.applier.apply_patch(sub_dir, patch_text)
        self.assertTrue(result)

    def test_module_level_apply_patch_function(self):
        patch_text = f"global_var = {random.randint(10, 99)}"
        result = apply_patch(self.target_file_path, patch_text)
        self.assertTrue(result)

    def test_io_error_handling_on_read(self):
        patch_text = f"test = {random.randint(1, 10)}"
        with patch('builtins.open', side_effect=IOError("Simulated read error")):
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(self.target_file_path, patch_text)

    def test_io_error_handling_on_write(self):
        patch_text = f"test = {random.randint(1, 10)}"
        orig_open = open
        def mock_open(*args, **kwargs):
            if len(args) > 1 and 'w' in args[1]:
                raise IOError("Simulated write error")
            return orig_open(*args, **kwargs)

        with patch('builtins.open', side_effect=mock_open):
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(self.target_file_path, patch_text)

    def test_dry_run_success(self):
        patch_text = f"z = {random.randint(1, 100)}"
        result = self.applier.dry_run(self.target_file_path, patch_text)
        self.assertTrue(result)
        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, self.random_content)

    def test_dry_run_file_not_found(self):
        non_existent = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.py")
        with self.assertRaises(PatchApplierError):
            self.applier.dry_run(non_existent, "z = 1")

    def test_rollback_success(self):
        backup_file = os.path.join(self.temp_dir, f"backup_{uuid.uuid4().hex}.bak")
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("original_data = 1\n")

        with open(self.target_file_path, 'w', encoding='utf-8') as f:
            f.write("modified_data = 2\n")

        result = self.applier.rollback(backup_file, self.target_file_path)
        self.assertTrue(result)
        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "original_data = 1\n")

    def test_rollback_non_existent_backup(self):
        non_existent = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.bak")
        with self.assertRaises(PatchApplierError):
            self.applier.rollback(non_existent, self.target_file_path)

    def test_read_patch_stream_variants(self):
        self.assertEqual(self.applier.read_patch_stream("test_patch"), "test_patch")
        self.assertEqual(self.applier.read_patch_stream(b"test_patch"), "test_patch")
        stream = io.BytesIO(b"test_stream")
        self.assertEqual(self.applier.read_patch_stream(stream), "test_stream")
        with self.assertRaises(PatchApplierError):
            self.applier.read_patch_stream(b'\x89PNG\r\n\x1a\n\xff\xff')

    def test_custom_backup_dir(self):
        backup_dir = os.path.join(self.temp_dir, "custom_backups")
        custom_applier = PatchApplier(self.repo_path, backup_dir=backup_dir)
        patch_text = "new_var = 42\n"
        result = custom_applier.apply_patch_with_backup(self.target_file_path, patch_text)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(backup_dir))
        self.assertTrue(len(os.listdir(backup_dir)) > 0)


if __name__ == '__main__':
    unittest.main()