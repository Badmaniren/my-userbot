import unittest
import uuid
import random
import os
import io
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.test_filename = f"test_target_{self.rand_suffix}.py"
        self.repo_path = os.getcwd()

        # Создаем реальный файл для интеграционного тестирования
        self.target_file_path = os.path.join(self.repo_path, self.test_filename)
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Initial content {self.rand_suffix}\nprint('hello')\n")

    def tearDown(self):
        if os.path.exists(self.target_file_path):
            try:
                os.remove(self.target_file_path)
            except OSError:
                pass

    def test_check_patch_integration_success(self):
        random_value = random.randint(1000, 9999)
        patch_content = f"""diff --git a/{self.test_filename} b/{self.test_filename}
--- a/{self.test_filename}
+++ b/{self.test_filename}
@@ -2,1 +2,2 @@
 print('hello')
+print('{random_value}')
"""
        checker = PatchChecker(repo_path=self.repo_path, policy={"strict_safety": True})
        result = checker.check_patch(patch_content=patch_content, target_file=self.test_filename)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)

    def test_check_empty_patch_raises_error(self):
        checker = PatchChecker(repo_path=self.repo_path)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch("")

    def test_check_file_integration(self):
        patch_file_name = f"patch_file_{self.rand_suffix}.diff"
        random_msg = f"msg_{uuid.uuid4().hex[:6]}"
        patch_file_content = f"""diff --git a/{self.test_filename} b/{self.test_filename}
--- a/{self.test_filename}
+++ b/{self.test_filename}
@@ -2,1 +2,2 @@
 print('hello')
+print('{random_msg}')
"""
        with open(patch_file_name, "w", encoding="utf-8") as f:
            f.write(patch_file_content)

        try:
            checker = PatchChecker(repo_path=self.repo_path)
            result = checker.check_file(patch_file_name, target_file=self.test_filename)
            self.assertIsInstance(result, dict)
            self.assertIn("is_valid", result)
        finally:
            if os.path.exists(patch_file_name):
                os.remove(patch_file_name)

    def test_check_stream_integration(self):
        random_id = uuid.uuid4().hex
        stream_content = f"""diff --git a/{self.test_filename} b/{self.test_filename}
--- a/{self.test_filename}
+++ b/{self.test_filename}
@@ -2,1 +2,2 @@
 print('hello')
+print('{random_id}')
"""
        stream = io.StringIO(stream_content)
        checker = PatchChecker(repo_path=self.repo_path)
        result = checker.check_stream(stream, target_file=self.test_filename)
        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)

    def test_convenience_function_check_patch(self):
        val = random.random()
        patch_content = f"""diff --git a/{self.test_filename} b/{self.test_filename}
--- a/{self.test_filename}
+++ b/{self.test_filename}
@@ -2,1 +2,2 @@
 print('hello')
+# {val}
"""
        result = check_patch(patch_content=patch_content, repo_path=self.repo_path, target_file=self.test_filename)
        self.assertIsInstance(result, dict)
        self.assertIn("risk_score", result)

    def test_check_method_dynamic_repo(self):
        checker = PatchChecker()
        patch_content = f"""diff --git a/{self.test_filename} b/{self.test_filename}
--- a/{self.test_filename}
+++ b/{self.test_filename}
@@ -2,1 +2,2 @@
 print('hello')
+print('dynamic')
"""
        result = checker.check(patch_content=patch_content, repo_path=self.repo_path, target_file=self.test_filename)
        self.assertIsInstance(result, dict)
        self.assertEqual(checker.repo_path, self.repo_path)


if __name__ == "__main__":
    unittest.main()