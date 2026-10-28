import unittest
import uuid
import random
import os
import io
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.test_filename = f"test_patch_{self.rand_suffix}.patch"
        self.sample_patch = f"""diff --git a/file_{self.rand_suffix}.py b/file_{self.rand_suffix}.py
--- a/file_{self.rand_suffix}.py
+++ b/file_{self.rand_suffix}.py
@@ -1,1 +1,2 @@
-# Test patch {self.rand_suffix}
+print("Hello {self.rand_suffix}")
"""

    def tearDown(self):
        if os.path.exists(self.test_filename):
            try:
                os.remove(self.test_filename)
            except OSError:
                pass

    def test_check_patch_valid_integration(self):
        checker = PatchChecker()
        result = checker.check_patch(self.sample_patch)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        self.assertIsInstance(result["risk_score"], float)

    def test_check_patch_empty_raises_error(self):
        checker = PatchChecker()
        empty_contents = ["", "   ", "\n\t "]
        content = random.choice(empty_contents)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(content)

    def test_check_file_integration(self):
        with open(self.test_filename, "w", encoding="utf-8") as f:
            f.write(self.sample_patch)

        checker = PatchChecker()
        result = checker.check_file(self.test_filename)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIsInstance(result["analysis"], dict)

    def test_check_stream_integration(self):
        stream = io.StringIO(self.sample_patch)
        checker = PatchChecker()
        result = checker.check_stream(stream)

        self.assertIn("is_safe", result)
        self.assertIn("evaluation", result)

    def test_check_method_with_policy_integration(self):
        strict_policy = {"strict_safety": True, "disallow_syntax_risks": True}
        checker = PatchChecker(policy=strict_policy)

        result = checker.check(self.sample_patch)
        self.assertIn("metrics", result)
        self.assertIn("policy_verdict", result)

    def test_functional_helper_check_patch(self):
        res = check_patch(patch_content=self.sample_patch, policy={"strict_safety": False})
        self.assertIsInstance(res, dict)
        self.assertIn("is_safe", res)

if __name__ == "__main__":
    unittest.main()