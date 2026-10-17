import unittest
import tempfile
import shutil
import uuid
import random
import os
from pathlib import Path

from skills.patch_auto_remediator import PatchAutoRemediator, PatchAutoRemediatorError
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.autonomous_engine import AutonomousEngine


class TestPatchAutoRemediatorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Initialize a minimal git repo structure using standard file system operations
        # as required for autonomous engine and git inspector integration.
        git_dir = os.path.join(self.repo_path, ".git")
        os.makedirs(git_dir, exist_ok=True)
        
        self.target_file_name = f"target_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        self.initial_content = f"# Initial state {uuid.uuid4().hex}\ndef compute():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_auto_remediator_composition_and_execution(self):
        unique_id = uuid.uuid4().hex[:8]
        random_value = random.randint(100, 999)
        
        patch_content = f"""diff --git a/{self.target_file_name} b/{self.target_file_name}
index 1234567..89abcdef 100644
--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -2,3 +2,3 @@
 def compute():
-    return 1
+    return {random_value}
 # {unique_id}
"""

        remediator = PatchAutoRemediator(repo_path=self.repo_path)
        
        self.assertTrue(hasattr(remediator, "patch_evaluator") or isinstance(remediator.evaluator, PatchEvaluator))
        self.assertTrue(hasattr(remediator, "autonomous_engine") or isinstance(remediator.engine, AutonomousEngine))

        try:
            result = remediator.remediate(patch_content=patch_content, target_file=self.target_file_name)
        except Exception as e:
            self.fail(f"PatchAutoRemediator.remediate raised an unexpected exception: {e}")

        self.assertIsNotNone(result)
        
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
            
        self.assertIn(unique_id, updated_content)
        self.assertIn(str(random_value), updated_content)


if __name__ == "__main__":
    unittest.main()