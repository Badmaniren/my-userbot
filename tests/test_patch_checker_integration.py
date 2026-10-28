import unittest
import uuid
import random
import os
import io
from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch

class TestPatchCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = f"./test_repo_{self.random_suffix}"
        os.makedirs(self.repo_path, exist_ok=True)

        self.target_filename = f"file_{self.random_suffix}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)

        self.initial_content = f"# Initial content {uuid.uuid4()}\nx = {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        if os.path.exists(self.target_file_path):
            os.remove(self.target_file_path)
        if os.path.exists(self.repo_path):
            os.rmdir(self.repo_path)

    def test_patch_checker_empty_content_raises_error(self):
        checker = PatchChecker(repo_path=self.repo_path)
        for empty_val in ["", "   ", "\n"]:
            with self.assertRaises(PatchCheckerError):
                checker.check_patch(patch_content=empty_val)

    def test_patch_checker_integration_flow(self):
        random_val = random.randint(1000, 9999)
        patch_content = f"--- a/{self.target_filename}\n+++ b/{self.target_filename}\n@@ -1,2 +1,2 @@\n-x = 1\n+x = {random_val}\n"

        policy = {"strict_safety": True, "disallow_syntax_risks": True}
        checker = PatchChecker(repo_path=self.repo_path, policy=policy)

        result = checker.check(patch_content=patch_content, repo_path=self.repo_path, target_file=self.target_filename)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        self.assertIn("metrics", result)

    def test_patch_checker_check_file_and_stream(self):
        temp_patch_filename = f"patch_{self.random_suffix}.diff"
        random_str = uuid.uuid4().hex
        patch_text = f"diff --git a/file.py b/file.py\n+ # {random_str}\n"

        with open(temp_patch_filename, "w", encoding="utf-8") as f:
            f.write(patch_text)

        try:
            checker = PatchChecker(repo_path=self.repo_path)
            file_result = checker.check_file(temp_patch_filename, target_file=self.target_filename)
            self.assertIsInstance(file_result, dict)
            self.assertIn("is_valid", file_result)

            with open(temp_patch_filename, "r", encoding="utf-8") as stream:
                stream_result = checker.check_stream(stream, target_file=self.target_filename)
                self.assertIsInstance(stream_result, dict)
                self.assertIn("is_safe", stream_result)
        finally:
            if os.path.exists(temp_patch_filename):
                os.remove(temp_patch_filename)

    def test_convenience_function(self):
        random_var_name = f"var_{uuid.uuid4().hex[:6]}"
        patch_content = f"+{random_var_name} = {random.randint(1, 500)}\n"

        result = check_patch(
            patch_content=patch_content,
            repo_path=self.repo_path,
            target_file=self.target_filename,
            policy={"strict_safety": False}
        )

        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)

if __name__ == "__main__":
    unittest.main()