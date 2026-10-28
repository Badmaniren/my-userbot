import unittest
import os
import tempfile
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.test_dir, self.file_name)

        self.initial_content = f"# Initial content {uuid.uuid4().hex}\nx = {random.randint(1, 100)}"
        with open(self.target_file_path, 'w', encoding='utf-8') as f:
            f.write(self.initial_content)

        self.applier = PatchApplier(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)

    def test_validate_patch_syntax_success(self):
        random_var = f"var_{uuid.uuid4().hex[:6]}"
        random_val = random.randint(100, 999)
        patch_content = f"{random_var} = {random_val}\n"

        result = self.applier.validate_patch_syntax(patch_content)
        self.assertTrue(result)

    def test_validate_patch_syntax_failure(self):
        invalid_patch = f"def broken_syntax_{uuid.uuid4().hex[:4]}():\n    print('Unclosed"

        with self.assertRaises(PatchApplierError):
            self.applier.validate_patch_syntax(invalid_patch)

    def test_apply_patch_unified_diff(self):
        new_line_value = f"added_line_{uuid.uuid4().hex[:6]}"
        patch_content = f"--- b/{self.file_name}\n+++ b/{self.file_name}\n@@ -1,2 +1,3 @@\n {self.initial_content}\n+{new_line_value}"

        result = self.applier.apply_patch(self.target_file_path, patch_content)
        self.assertTrue(result)

        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(new_line_value, content)

    def test_apply_patch_with_backup(self):
        replacement_text = f"completely_new_{uuid.uuid4().hex}"
        patch_content = f"x = '{replacement_text}'"

        result = self.applier.apply_patch_with_backup(self.target_file_path, patch_content)
        self.assertTrue(result)

        backup_files = [f for f in os.listdir(self.test_dir) if '.bak_' in f]
        self.assertTrue(len(backup_files) > 0, "Backup file should be created.")

        backup_file_path = os.path.join(self.test_dir, backup_files[0])
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()

        self.assertEqual(backup_content, self.initial_content)

    def test_functional_wrapper_apply_patch(self):
        wrapper_text = f"wrapper_test_{uuid.uuid4().hex[:8]}"
        patch_content = f"y = '{wrapper_text}'"

        result = apply_patch(self.target_file_path, patch_content)
        self.assertTrue(result)

        with open(self.target_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(wrapper_text, content)

    def test_apply_patch_file_not_found(self):
        non_existent_path = os.path.join(self.test_dir, f"missing_{uuid.uuid4().hex}.py")
        patch_content = "print('test')"

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(non_existent_path, patch_content)


if __name__ == '__main__':
    unittest.main()