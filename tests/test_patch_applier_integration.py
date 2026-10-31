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
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test Architect"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "init_file.txt"
        self.initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write("Initial state\n")
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_applier_and_git_inspector_integration(self):
        random_tag = f"backup-{uuid.uuid4().hex[:8]}"
        random_file_name = f"feature_{uuid.uuid4().hex[:6]}.py"
        random_content = f"# Autonomous generated code id: {uuid.uuid4()}\nprint('OK')"

        patch_data = {
            "file_path": random_file_name,
            "content": random_content,
            "backup_id": random_tag
        }

        success = apply_patch(self.test_dir, patch_data)
        self.assertTrue(success)

        target_file_path = os.path.join(self.test_dir, random_file_name)
        self.assertTrue(os.path.exists(target_file_path))

        with open(target_file_path, "r", encoding="utf-8") as f:
            content_read = f.read()
        self.assertEqual(content_read, random_content)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2)

        applier = PatchApplier(self.test_dir)
        applier.rollback(random_tag)

        self.assertFalse(os.path.exists(target_file_path))
        
        applier.verify_repository_state()