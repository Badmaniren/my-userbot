import unittest
import uuid
import random
import os
import io
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_id = str(uuid.uuid4())
        self.risk_val = round(random.uniform(0.1, 0.9), 2)
        self.sample_patch = f"""diff --git a/test_{self.random_id}.py b/test_{self.random_id}.py
new file mode 100644
index 0000000..8304b6f
--- /dev/null
+++ b/test_{self.random_id}.py
@@ -0,0 +1,2 @@
+print("Integration test {self.random_id}")
+risk_metric = {self.risk_val}
"""

    def test_patch_checker_success_flow(self):
        policy = {"strict_safety": True, "disallow_syntax_risks": True}
        checker = PatchChecker(policy=policy)
        
        result = checker.check_patch(self.sample_patch)
        
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        
        analysis = result["analysis"]
        self.assertIsInstance(analysis, dict)
        
        evaluation = result["evaluation"]
        self.assertIsInstance(evaluation, dict)
        self.assertIn("metrics", evaluation)

    def test_patch_checker_empty_patch_error(self):
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("   ")

    def test_patch_checker_file_io(self):
        file_name = f"temp_patch_{self.random_id}.diff"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.sample_patch)
            
            checker = PatchChecker()
            result = checker.check_file(file_name)
            
            self.assertIn("analysis", result)
            self.assertIn("evaluation", result)
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    def test_patch_checker_stream_io(self):
        stream = io.StringIO(self.sample_patch)
        checker = PatchChecker()
        result = checker.check_stream(stream)
        
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)

    def test_convenience_function(self):
        result = check_patch(
            patch_content=self.sample_patch,
            policy={"strict_safety": False, "max_risk_score": 1.0}
        )
        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)

    def test_integration_max_risk_score_policy(self):
        checker = PatchChecker(policy={"max_risk_score": -0.1})
        result = checker.check_patch(self.sample_patch)
        self.assertIn("policy_verdict", result)
        self.assertIn("disallowed_risks", result["policy_verdict"])

if __name__ == "__main__":
    unittest.main()