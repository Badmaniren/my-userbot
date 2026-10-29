import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import io
import os

from skills.patch_applier import PatchApplier, PatchApplierError


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    def test_apply_patch_success(self):
        target_file = f"{uuid.uuid4().hex}.py"
        patch_content = f"# {uuid.uuid4().hex}\nprint('{uuid.uuid4().hex}')"
        original_content = f"print('{uuid.uuid4().hex}')"

        mock_file_data = io.StringIO(original_content)

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=original_content)) as mock_file, \
             patch('subprocess.run') as mock_run:

            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = uuid.uuid4().hex.encode('utf-8')

            result = self.applier.apply_patch(target_file, patch_content)

            self.assertTrue(result)
            mock_file.assert_any_call(os.path.join(self.repo_path, target_file), 'r', encoding='utf-8')
            mock_run.assert_called()

    def test_apply_patch_file_not_found(self):
        target_file = f"{uuid.uuid4().hex}.py"
        patch_content = f"print('{uuid.uuid4().hex}')"

        with patch('os.path.exists', return_value=False):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(target_file, patch_content)

            self.assertIn(target_file, str(ctx.exception))

    def test_apply_patch_subprocess_failure(self):
        target_file = f"{uuid.uuid4().hex}.py"
        patch_content = f"print('{uuid.uuid4().hex}')"
        original_content = f"pass\n"

        error_message = uuid.uuid4().hex

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=original_content)), \
             patch('subprocess.run') as mock_run:

            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = error_message.encode('utf-8')

            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(target_file, patch_content)

            self.assertIn(error_message, str(ctx.exception))

    def test_rollback_patch_success(self):
        backup_file = f"{uuid.uuid4().hex}.bak"
        target_file = f"{uuid.uuid4().hex}.py"
        backup_content = ''.join(random.choices(string.ascii_letters, k=50))

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=backup_content)) as mock_file, \
             patch('shutil.copy') as mock_copy:

            result = self.applier.rollback_patch(target_file, backup_file)

            self.assertTrue(result)
            mock_copy.assert_called_once()

    def test_rollback_patch_missing_backup(self):
        backup_file = f"{uuid.uuid4().hex}.bak"
        target_file = f"{uuid.uuid4().hex}.py"

        with patch('os.path.exists', return_value=False):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.rollback_patch(target_file, backup_file)

            self.assertIn(backup_file, str(ctx.exception))

    def test_sanitize_and_apply_integration(self):
        target_file = f"{uuid.uuid4().hex}.py"
        raw_patch = f"def fn_{uuid.uuid4().hex}():\n    return '{uuid.uuid4().hex}'"

        with patch('skills.patch_applier.PatchApplier.apply_patch', return_value=True) as mock_apply:
            result = self.applier.sanitize_and_apply(target_file, raw_patch)
            self.assertTrue(result)
            mock_apply.assert_called_once()
            args, _ = mock_apply.call_args
            self.assertEqual(args[0], target_file)
            self.assertIn(raw_patch, args[1])


if __name__ == '__main__':
    unittest.main()