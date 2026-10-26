import unittest
import uuid
import random
import os
import io
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.test_filename = f"test_target_{self.random_suffix}.py"
        self.risk_value = round(random.uniform(0.1, 0.9), 2)
        
        self.valid_patch = (
            f"diff --git a/{self.test_filename} b/{self.test_filename}\n"
            f"--- a/{self.test_filename}\n"
            f"+++ b/{self.test_filename}\n"
            f"@@ -1,1 +1,2 @@\n"
            f" # Initial content\n"
            f"+# Added line {self.random_suffix}\n"
        )

    def tearDown(self):
        if os.path.exists(self.test_filename):
            try:
                os.remove(self.test_filename)
            except OSError:
                pass

    def test_patch_checker_empty_content_raises_error(self):
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")

    def test_patch_checker_integration_with_real_analyzer_and_evaluator(self):
        checker = PatchChecker(policy={"strict_safety": False})
        result = checker.check_patch(patch_content=self.valid_patch)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)

    def test_patch_checker_with_file_input(self):
        with open(self.test_filename, "w", encoding="utf-8") as f:
            f.write(self.valid_patch)

        checker = PatchChecker()
        result = checker.check_file(self.test_filename)

        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)

    def test_patch_checker_with_stream_input(self):
        stream = io.StringIO(self.valid_patch)
        checker = PatchChecker()
        result = checker.check_stream(stream)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation", result)

    def test_check_function_wrapper(self):
        result = check_patch(patch_content=self.valid_patch, policy={"disallow_syntax_risks": True})
        self.assertIsInstance(result, dict)
        self.assertIn("policy_verdict", result)

    def test_dynamic_repo_path_switch(self):
        checker = PatchChecker()
        new_repo_path = f"./repo_{self.random_suffix}"
        result = checker.check(patch_content=self.valid_patch, repo_path=new_repo_path)
        
        self.assertEqual(checker.repo_path, new_repo_path)
        self.assertIn("metrics", result)

if __name__ == "__main__":
    unittest.main()