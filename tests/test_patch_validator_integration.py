import unittest
import uuid
import random
import tempfile
import os

from skills.patch_validator import validate_patch
from skills.code_validator import CodeValidatorError
from skills.code_sanitizer import CodeSanitizerError


class TestPatchValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.unique_id = str(uuid.uuid4())
        self.random_metric = random.randint(100, 9999)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_patch_validator_integration_valid_syntax(self):
        valid_code_snippet = f"""
# Unique ID: {self.unique_id}
# Metric: {self.random_metric}

def compute_value():
    x = {self.random_metric}
    return x * 2
"""
        patch_content = f"""diff --git a/module.py b/module.py
--- a/module.py
+++ b/module.py
@@ -1,3 +1,6 @@
+# Unique ID: {self.unique_id}
+# Metric: {self.random_metric}
+
 def compute_value():
-    pass
+    x = {self.random_metric}
+    return x * 2
"""

        file_path = os.path.join(self.repo_path, f"test_target_{self.unique_id}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("def compute_value():\n    pass\n")

        result = validate_patch(patch_content, target_path=file_path)

        self.assertIsInstance(result, dict)
        self.assertIn("is_valid", result)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result.get("unique_identifier"), self.unique_id)

    def test_patch_validator_integration_malicious_security(self):
        malicious_code = f"""
import os
os.system("echo {self.unique_id}")
"""
        patch_content = f"""diff --git a/danger.py b/danger.py
--- a/danger.py
+++ b/danger.py
@@ -0,0 +1,3 @@
+import os
+os.system("echo {self.unique_id}")
"""

        file_path = os.path.join(self.repo_path, f"danger_{self.unique_id}.py")

        result = validate_patch(patch_content, target_path=file_path)

        self.assertIsInstance(result, dict)
        self.assertIn("is_valid", result)
        self.assertFalse(result["is_valid"])
        self.assertIn("security_violation", result.get("error_type", ""))


if __name__ == "__main__":
    unittest.main()