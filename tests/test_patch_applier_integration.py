import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_applier import apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@system.local'")
        
        self.target_file = os.path.join(self.test_dir, "target.py")
        self.unique_content = f"print('{uuid.uuid4()}')\n"
        with open(self.target_file, "w") as f:
            f.write(self.unique_content)
            
        os.system(f"git -C {self.test_dir} add target.py")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_patch_applier_flow(self):
        random_suffix = uuid.uuid4().hex[:8]
        patch_content = f"print('{random_suffix}')\n"
        
        patch_data = {
            "file_path": "target.py",
            "content": patch_content,
            "backup_id": str(uuid.uuid4())
        }

        result = apply_patch(self.test_dir, patch_data)
        
        self.assertTrue(result, "Patch applier should return success status.")

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        
        self.assertGreaterEqual(len(history), 1, "Repository history must contain commits after applying patch.")

        with open(self.target_file, "r") as f:
            updated_data = f.read()

        self.assertIn(random_suffix, updated_data, "Target file must contain the applied patch data.")


if __name__ == "__main__":
    unittest.main()