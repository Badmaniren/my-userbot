import unittest
import uuid
import random
import io
import os
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_id = str(uuid.uuid4())
        self.test_filename = f"test_target_{self.random_id}.py"
        self.sample_code = f"def generated_func_{self.random_id.replace('-', '_')}():\n    return '{self.random_id}'\n"
        
        with open(self.test_filename, "w", encoding="utf-8") as f:
            f.write(self.sample_code)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_patch_checker_empty_input(self):
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")

    def test_patch_checker_real_integration(self):
        unique_string = f"val_{random.randint(1000, 9999)}_{self.random_id}"
        patch_content = f"""--- {self.test_filename}
+++ {self.test_filename}
@@ -1,2 +1,3 @@
 def generated_func():
     return '{unique_string}'
+    # Extra verified comment {random.random()}
"""
        policy = {
            "strict_safety": False,
            "disallow_syntax_risks": True
        }
        
        checker = PatchChecker(policy=policy)
        result = checker.check(patch_content=patch_content, target_file=self.test_filename)
        
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        self.assertIsInstance(result["risk_score"], float)

    def test_check_file_and_stream(self):
        checker = PatchChecker()
        
        # Test check_file
        file_result = checker.check_file(self.test_filename, target_file=self.test_filename)
        self.assertIsInstance(file_result, dict)
        self.assertIn("is_valid", file_result)

        # Test check_stream
        with open(self.test_filename, "r", encoding="utf-8") as f:
            stream_result = checker.check_stream(f, target_file=self.test_filename)
            self.assertIsInstance(stream_result, dict)
            self.assertIn("is_safe", stream_result)

    def test_functional_helper(self):
        patch_content = f"""--- {self.test_filename}
+++ {self.test_filename}
@@ -1,2 +1,2 @@
-def generated_func():
+def updated_func_{random.randint(100, 999)}():
     pass
"""
        res = check_patch(patch_content=patch_content, target_file=self.test_filename)
        self.assertIsInstance(res, dict)
        self.assertIn("analysis", res)

if __name__ == "__main__":
    unittest.main()