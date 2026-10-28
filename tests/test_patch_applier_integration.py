import os
import io
import tempfile
import shutil
import unittest
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_patch_applier_integration_")
        self.backup_dir = os.path.join(self.temp_dir, ".backups")
        self.applier = PatchApplier(repo_path=self.temp_dir, backup_dir=self.backup_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_patch_application_and_rollback_workflow(self):
        sub_dir = os.path.join(self.temp_dir, "subdir")
        target_file = os.path.join(sub_dir, "module.py")

        initial_content = "def original_func():\n    return 'original'\n"
        os.makedirs(sub_dir, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        patched_content = "def patched_func():\n    return 'updated'\n"
        result = self.applier.apply_patch(patched_content, target_path=target_file)

        self.assertTrue(result["success"])
        backup_id = result["backup_id"]
        self.assertEqual(result["target"], target_file)

        with open(target_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), patched_content)

        self.assertIn(backup_id, self.applier.backups)

        rollback_success = self.applier.rollback(backup_id)
        self.assertTrue(rollback_success)

        with open(target_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), initial_content)

        self.assertNotIn(backup_id, self.applier.backups)

    def test_create_new_file_in_nested_directory(self):
        new_file = os.path.join(self.temp_dir, "nested", "deep", "new_file.py")
        patch_content = "# CREATE new file\ndef new_feature():\n    pass\n"

        result = self.applier.apply_patch(patch_content, target_path=new_file)
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(new_file))

        with open(new_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), patch_content)

    def test_dry_run_and_stream_processing_integration(self):
        target_file = os.path.join(self.temp_dir, "dry_test.txt")
        original_text = "line 1\nline 2\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(original_text)

        stream = io.BytesIO(b"line 1\nline 2 modified\n")
        dry_run_res = self.applier.read_patch_stream(stream)

        self.assertTrue(dry_run_res["success"])
        self.assertTrue(dry_run_res["dry_run"])

        with open(target_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), original_text)

    def test_invalid_patch_and_error_handling(self):
        invalid_patch = "INVALID_PATCH_FORMAT"
        target_file = os.path.join(self.temp_dir, "file.txt")

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(invalid_patch, target_path=target_file)

        fake_id = uuid.uuid4().hex
        with self.assertRaises(PatchApplierError):
            self.applier.rollback(fake_id)


if __name__ == "__main__":
    unittest.main()
