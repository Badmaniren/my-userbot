import unittest
import uuid
import random
import io
import os
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_evaluator import PatchEvaluator

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.test_filename = f"test_target_{self.random_suffix}.py"
        self.test_file_path = os.path.abspath(self.test_filename)

        self.sample_code = f"def generated_func_{self.random_suffix}():\n    return {random.randint(100, 999)}"
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.sample_code)

        self.valid_patch = f"""--- {self.test_filename}
+++ {self.test_filename}
@@ -1,2 +1,3 @@
 def generated_func_{self.random_suffix}():
+    # random comment {uuid.uuid4()}
     return {random.randint(100, 999)}
"""

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_patch_checker_empty_raises_error(self):
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("   ")

    def test_patch_checker_integration_workflow(self):
        policy = {
            "strict_safety": True,
            "disallow_syntax_risks": True
        }
        checker = PatchChecker(repo_path=os.getcwd(), policy=policy)
        
        result = checker.check_patch(patch_content=self.valid_patch, target_file=self.test_filename)
        
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        
        self.assertIsInstance(result["risk_score"], float)

    def test_patch_checker_file_and_stream(self):
        checker = PatchChecker(repo_path=os.getcwd())

        patch_file_name = f"patch_{self.random_suffix}.diff"
        with open(patch_file_name, "w", encoding="utf-8") as f:
            f.write(self.valid_patch)
            
        try:
            file_result = checker.check_file(file_path=patch_file_name, target_file=self.test_filename)
            self.assertIn("is_valid", file_result)
            
            with open(patch_file_name, "r", encoding="utf-8") as stream_f:
                stream_result = checker.check_stream(stream=stream_f, target_file=self.test_filename)
                self.assertIn("is_safe", stream_result)
        finally:
            if os.path.exists(patch_file_name):
                os.remove(patch_file_name)

    def test_patch_checker_convenience_function(self):
        result = check_patch(
            patch_content=self.valid_patch,
            repo_path=os.getcwd(),
            target_file=self.test_filename,
            policy={"strict_safety": False}
        )
        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertIn("metrics", result)

if __name__ == "__main__":
    unittest.main()