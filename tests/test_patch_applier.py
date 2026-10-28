import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import string

from skills.patch_applier import PatchApplier, PatchApplierError


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    def test_apply_patch_success(self):
        target_file = f"{uuid.uuid4().hex}.py"
        file_content = ''.join(random.choices(string.ascii_letters + ' ', k=50))
        patch_content = ''.join(random.choices(string.ascii_letters + ' ', k=30))

        mock_file_handle = mock_open(read_data=file_content)

        with patch("builtins.open", mock_file_handle) as mock_file, \
             patch("os.path.exists", return_value=True), \
             patch("os.makedirs") as mock_makedirs:

            full_path = self.applier._resolve_path(target_file)
            result = self.applier.apply_patch(target_file, patch_content)

            self.assertTrue(result)
            mock_file.assert_any_call(full_path, 'r', encoding='utf-8')
            mock_file.assert_any_call(full_path, 'w', encoding='utf-8')

    def test_apply_patch_file_not_found(self):
        target_file = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        patch_content = uuid.uuid4().hex

        with patch("os.path.exists", return_value=False):
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(target_file, patch_content)

    def test_apply_patch_io_error(self):
        target_file = f"{uuid.uuid4().hex}.py"
        patch_content = uuid.uuid4().hex

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):

            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(target_file, patch_content)

    def test_rollback_patch_success(self):
        backup_file = f"/tmp/{uuid.uuid4().hex}.bak"
        target_file = f"/tmp/{uuid.uuid4().hex}.py"
        backup_data = uuid.uuid4().hex.encode('utf-8')

        with patch("os.path.exists", return_value=True), \
             patch("shutil.copyfile") as mock_copy, \
             patch("builtins.open", mock_open(read_data=backup_data)) as mock_file:

            result = self.applier.rollback_patch(target_file, backup_file)
            self.assertTrue(result)
            mock_copy.assert_called_once_with(backup_file, target_file)

    def test_rollback_patch_missing_backup(self):
        backup_file = f"/tmp/{uuid.uuid4().hex}.bak"
        target_file = f"/tmp/{uuid.uuid4().hex}.py"

        with patch("os.path.exists", return_value=False):
            with self.assertRaises(PatchApplierError):
                self.applier.rollback_patch(target_file, backup_file)

    def test_verify_syntax_valid(self):
        code_snippet = f"def {uuid.uuid4().hex}():\n    pass"

        with patch("builtins.open", mock_open(read_data=code_snippet)):
            result = self.applier.verify_syntax(uuid.uuid4().hex)
            self.assertTrue(result)

    def test_verify_syntax_invalid(self):
        bad_code_snippet = f"def {uuid.uuid4().hex}("

        with patch("builtins.open", mock_open(read_data=bad_code_snippet)):
            with self.assertRaises(PatchApplierError):
                self.applier.verify_syntax(uuid.uuid4().hex)

    def test_stream_patch_application(self):
        stream_data = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(stream_data)
        target_file = f"{uuid.uuid4().hex}.py"

        with patch("builtins.open", mock_open()) as mock_file:
            result = self.applier.apply_patch_from_stream(target_file, mock_stream)
            self.assertTrue(result)
            mock_file().write.assert_called()


if __name__ == '__main__':
    unittest.main()