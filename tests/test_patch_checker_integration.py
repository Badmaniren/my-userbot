import unittest
import uuid
import random
import os
import io

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_evaluator import PatchEvaluator

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = f"./test_repo_{self.random_suffix}"
        os.makedirs(self.repo_path, exist_ok=True)

        self.target_file_name = f"target_{self.random_suffix}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        self.original_content = f"# Initial version {uuid.uuid4()}\ndef foo():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.original_content)

    def tearDown(self):
        if os.path.exists(self.target_file_path):
            os.remove(self.target_file_path)
        if os.path.exists(self.repo_path):
            os.rmdir(self.repo_path)

    def test_integration_check_patch_real_execution(self):
        random_value = random.randint(101, 999)
        patch_content = f"""--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -2,2 +2,2 @@
 def foo():
-    return 1
+    return {random_value}
"""
        policy = {
            "strict_safety": True,
            "disallow_syntax_risks": True
        }

        checker = PatchChecker(repo_path=self.repo_path, policy=policy)
        result = checker.check_patch(patch_content=patch_content, target_file=self.target_file_name)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)

    def test_integration_check_file_and_stream(self):
        random_value = random.randint(1000, 9999)
        patch_content = f"""--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -2,2 +2,2 @@
 def foo():
-    return 1
+    return {random_value}
"""
        temp_patch_file = f"./patch_{self.random_suffix}.diff"
        with open(temp_patch_file, "w", encoding="utf-8") as f:
            f.write(patch_content)

        try:
            checker = PatchChecker(repo_path=self.repo_path)

            file_result = checker.check_file(temp_patch_file, target_file=self.target_file_name)
            self.assertIsInstance(file_result, dict)
            self.assertTrue(file_result.get("is_safe", True))

            stream = io.StringIO(patch_content)
            stream_result = checker.check_stream(stream, target_file=self.target_file_name)
            self.assertIsInstance(stream_result, dict)
            self.assertIn("analysis", stream_result)

        finally:
            if os.path.exists(temp_patch_file):
                os.remove(temp_patch_file)

    def test_integration_helper_function_and_exceptions(self):
        empty_patch = "   "
        with self.assertRaises(PatchCheckerError):
            check_patch(patch_content=empty_patch, repo_path=self.repo_path)

        random_value = random.randint(10000, 99999)
        patch_content = f"""--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -2,2 +2,2 @@
 def foo():
-    return 1
+    return {random_value}
"""
        res = check_patch(patch_content=patch_content, repo_path=self.repo_path, target_file=self.target_file_name)
        self.assertIsInstance(res, dict)
        self.assertIn("risk_score", res)

if __name__ == "__main__":
    unittest.main()