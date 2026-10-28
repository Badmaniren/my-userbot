import unittest
import uuid
import random
import os
import tempfile
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.rand_str = str(uuid.uuid4())

        self.target_file_name = f"test_file_{random.randint(1000, 9999)}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(f"print('Initial {self.rand_str}')\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_patch_checker_integration_real_execution(self):
        patch_uid = str(uuid.uuid4())
        diff_content = f"""diff --git a/{self.target_file_name} b/{self.target_file_name}
index 1111111..2222222 100644
--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -1,1 +1,2 @@
 print('Initial {self.rand_str}')
+print('Updated {patch_uid}')
"""

        checker = PatchChecker(repo_path=self.repo_path, policy={"strict_safety": False})

        result = checker.check(patch_content=diff_content, repo_path=self.repo_path, target_file=self.target_file_name)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)

        file_check_result = checker.check_file(self.target_file_path, target_file=self.target_file_name)
        self.assertIsInstance(file_check_result, dict)

        func_result = check_patch(patch_content=diff_content, repo_path=self.repo_path, target_file=self.target_file_name)
        self.assertIsInstance(func_result, dict)
        self.assertIn("risk_score", func_result)

    def test_patch_checker_empty_patch_error(self):
        checker = PatchChecker(repo_path=self.repo_path)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")

    def test_patch_checker_file_not_found(self):
        checker = PatchChecker(repo_path=self.repo_path)
        non_existent = os.path.join(self.repo_path, f"missing_{uuid.uuid4()}.py")
        with self.assertRaises(PatchCheckerError):
            checker.check_file(non_existent)

if __name__ == "__main__":
    unittest.main()