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
        
        self.initial_file = "test_file.txt"
        self.random_content = f"initial content {uuid.uuid4()}"
        file_path = os.path.join(self.test_dir, self.initial_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content + "\n")
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_safe_apply_and_rollback_integration(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"

        random_patch_content = f"new patch line {uuid.uuid4()}"
        patch_file_name = f"patch_{uuid.uuid4().hex[:8]}.patch"
        patch_file_path = os.path.join(self.test_dir, patch_file_name)

        patch_data = (
            f"diff --git a/{self.initial_file} b/{self.initial_file}\n"
            f"--- a/{self.initial_file}\n"
            f"+++ b/{self.initial_file}\n"
            f"@@ -1,1 +1,2 @@\n"
            f"-{self.random_content}\n"
            f"+{self.random_content}\n"
            f"+{random_patch_content}\n"
        )

        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(patch_data)

        applier.safe_apply(patch_file_name, backup_tag)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertTrue(len(history) > 0)

        with open(os.path.join(self.test_dir, self.initial_file), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(random_patch_content, content)

        applier.rollback(backup_tag)

        with open(os.path.join(self.test_dir, self.initial_file), "r", encoding="utf-8") as f:
            rolled_back_content = f.read()
        self.assertNotIn(random_patch_content, rolled_back_content)

    def test_apply_patch_dict_integration(self):
        random_file_name = f"dir_{uuid.uuid4().hex[:6]}/feature_{uuid.uuid4().hex[:6]}.py"
        random_text = f"print('{uuid.uuid4()}')"
        backup_id = f"id_{uuid.uuid4().hex[:8]}"

        patch_dict = {
            "file_path": random_file_name,
            "content": random_text,
            "backup_id": backup_id
        }

        result = apply_patch(self.test_dir, patch_dict)
        self.assertTrue(result)

        target_file = os.path.join(self.test_dir, random_file_name)
        self.assertTrue(os.path.exists(target_file))

        with open(target_file, "r", encoding="utf-8") as f:
            saved_content = f.read()
        self.assertEqual(saved_content, random_text)

        applier = PatchApplier(self.test_dir)
        self.assertTrue(applier.verify_repository_state())

    def test_patch_applier_error_handling(self):
        applier = PatchApplier(self.test_dir)
        non_existent_patch = f"missing_{uuid.uuid4()}.patch"
        backup_tag = f"err_backup_{uuid.uuid4().hex[:8]}"

        with self.assertRaises(PatchApplierError):
            applier.safe_apply(non_existent_patch, backup_tag)


if __name__ == "__main__":
    unittest.main()