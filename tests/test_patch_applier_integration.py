import unittest
import tempfile
import shutil
import os
import uuid
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector

class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect Test"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True)
        
        self.initial_file = os.path.join(self.test_dir, "README.md")
        self.random_content = f"Initial content {uuid.uuid4()}"
        with open(self.initial_file, "w", encoding="utf-8") as f:
            f.write(self.random_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", "README.md"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_safe_apply_and_rollback(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup-{uuid.uuid4().hex[:8]}"
        
        target_file = "README.md"
        new_content = f"Updated content {uuid.uuid4()}"
        patch_data = {
            "file_path": target_file,
            "content": new_content,
            "backup_id": backup_tag
        }

        result = apply_patch(self.test_dir, patch_data)
        self.assertTrue(result)

        full_target_path = os.path.join(self.test_dir, target_file)
        with open(full_target_path, "r", encoding="utf-8") as f:
            content_on_disk = f.read()
        self.assertEqual(content_on_disk, new_content)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=2)
        self.assertTrue(len(history) >= 2)

        bad_backup_tag = f"bad-backup-{uuid.uuid4().hex[:8]}"
        applier.create_recovery_point(bad_backup_tag)

        broken_content = f"Broken content {uuid.uuid4()}"
        with open(full_target_path, "w", encoding="utf-8") as f:
            f.write(broken_content)

        applier.rollback(bad_backup_tag)
        
        with open(full_target_path, "r", encoding="utf-8") as f:
            reverted_content = f.read()
        self.assertEqual(reverted_content, new_content)

    def test_integration_patch_applier_error_handling(self):
        applier = PatchApplier(self.test_dir)
        invalid_tag = f"nonexistent-{uuid.uuid4()}"

        with self.assertRaises(PatchApplierError):
            applier.rollback(invalid_tag)

        with self.assertRaises(PatchApplierError):
            applier.apply_patch(os.path.join(self.test_dir, f"missing-{uuid.uuid4()}.patch"))