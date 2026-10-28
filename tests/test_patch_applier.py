import unittest
import os
import io
import shutil
import tempfile
import uuid
import random
import string
from unittest.mock import patch, MagicMock, mock_open

from skills.patch_applier import PatchApplier, PatchApplierError


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix=f"test_repo_{uuid.uuid4().hex[:8]}_")
        self.backup_dir = os.path.join(self.temp_dir, f"backups_{uuid.uuid4().hex[:6]}")
        self.applier = PatchApplier(repo_path=self.temp_dir, backup_dir=self.backup_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _random_str(self, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_init_custom_paths(self):
        custom_repo = os.path.join(tempfile.gettempdir(), f"repo_{uuid.uuid4().hex}")
        custom_backup = os.path.join(custom_repo, f"bak_{uuid.uuid4().hex}")
        applier = PatchApplier(repo_path=custom_repo, backup_dir=custom_backup)
        self.assertEqual(applier.repo_path, custom_repo)
        self.assertEqual(applier.backup_dir, custom_backup)

    def test_dry_run_success_no_file_modification(self):
        filename = f"file_{uuid.uuid4().hex}.txt"
        target_path = os.path.join(self.temp_dir, filename)
        initial_content = f"content_{uuid.uuid4().hex}"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        patch_text = f"PATCH_ADD_{uuid.uuid4().hex}"
        result = self.applier.dry_run(patch_text, target_path=target_path)

        self.assertTrue(result.get("success"))
        self.assertTrue(result.get("dry_run"))

        with open(target_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(current_content, initial_content)

    def test_dry_run_invalid_patch_raises_error(self):
        invalid_patch = f"INVALID_{uuid.uuid4().hex}"
        with self.assertRaises(PatchApplierError):
            self.applier.dry_run(invalid_patch)

    def test_apply_patch_modifies_target_file_and_creates_backup(self):
        filename = f"target_{uuid.uuid4().hex}.py"
        target_path = os.path.join(self.temp_dir, filename)
        initial_content = f"def old_func_{uuid.uuid4().hex}(): return {random.randint(100, 999)}"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        new_content = f"def new_func_{uuid.uuid4().hex}(): return {random.randint(1000, 9999)}"
        result = self.applier.apply_patch(new_content, target_path=target_path)

        self.assertTrue(result["success"])
        backup_id = result["backup_id"]
        self.assertIsNotNone(backup_id)

        with open(target_path, "r", encoding="utf-8") as f:
            modified_content = f.read()

        self.assertEqual(modified_content, new_content)
        self.assertNotEqual(modified_content, initial_content)

    def test_rollback_restores_file_state(self):
        filename = f"code_{uuid.uuid4().hex}.py"
        target_path = os.path.join(self.temp_dir, filename)
        initial_code = f"VAR_{self._random_str(8)} = '{self._random_str(16)}'"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(initial_code)

        patched_code = f"VAR_{self._random_str(8)} = '{self._random_str(16)}'"
        res = self.applier.apply_patch(patched_code, target_path=target_path)
        backup_id = res["backup_id"]

        rollback_res = self.applier.rollback(backup_id)
        self.assertTrue(rollback_res)

        with open(target_path, "r", encoding="utf-8") as f:
            restored_code = f.read()

        self.assertEqual(restored_code, initial_code)

    def test_rollback_non_existent_backup_raises_error(self):
        fake_backup_id = f"nonexistent_{uuid.uuid4().hex}"
        with self.assertRaises(PatchApplierError):
            self.applier.rollback(fake_backup_id)

    def test_apply_patch_non_existent_file_without_create_flag(self):
        non_existent_path = os.path.join(self.temp_dir, f"missing_{uuid.uuid4().hex}.py")
        patch_text = f"DIFF_{self._random_str(10)}"

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(patch_text, target_path=non_existent_path)

    def test_apply_patch_with_dry_run_flag(self):
        filename = f"dry_target_{uuid.uuid4().hex}.txt"
        target_path = os.path.join(self.temp_dir, filename)
        content = f"INITIAL_{uuid.uuid4().hex}"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        patch_data = f"PATCH_{uuid.uuid4().hex}"
        result = self.applier.apply_patch(patch_data, target_path=target_path, dry_run=True)

        self.assertTrue(result["dry_run"])
        with open(target_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_read_patch_from_bytes_stream(self):
        random_bytes_content = f"VALID_PATCH_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes_content)

        if hasattr(self.applier, 'read_patch_stream'):
            res = self.applier.read_patch_stream(stream)
            self.assertTrue(res.get("success"))

    def test_mocked_file_system_operations(self):
        target_file = os.path.join(self.temp_dir, f"mocked_{uuid.uuid4().hex}.py")
        rand_text = f"MOCKED_CONTENT_{uuid.uuid4().hex}"

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data=rand_text)):
                result = self.applier.dry_run(rand_text, target_path=target_file)
                self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()