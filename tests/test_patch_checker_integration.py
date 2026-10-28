import io
import os
import tempfile
import unittest
import uuid

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch


class TestPatchCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def _generate_diff(self, file_name: str = None, old_val: str = None, new_val: str = None) -> str:
        uid = uuid.uuid4().hex[:8]
        file_name = file_name or f"test_module_{uid}.py"
        old_val = old_val or f"old_value_{uid}"
        new_val = new_val or f"new_value_{uid}"

        return (
            f"--- a/{file_name}\n"
            f"+++ b/{file_name}\n"
            "@@ -1,3 +1,3 @@\n"
            f" def func_{uid}():\n"
            f"-    val = '{old_val}'\n"
            f"+    val = '{new_val}'\n"
            "     return val\n"
        )

    def test_check_patch_valid_integration(self):
        filename = f"sample_{uuid.uuid4().hex[:6]}.py"
        patch_content = self._generate_diff(file_name=filename)

        checker = PatchChecker(repo_path=self.repo_path)
        result = checker.check_patch(patch_content, target_file=filename)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertIn("risk_score", result)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)

        self.assertIsInstance(result["is_safe"], bool)
        self.assertIsInstance(result["is_valid"], bool)
        self.assertIsInstance(result["risk_score"], (int, float))
        self.assertIsInstance(result["analysis"], dict)
        self.assertIsInstance(result["evaluation"], dict)

    def test_check_patch_empty_content_raises_error(self):
        checker = PatchChecker(repo_path=self.repo_path)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch("   \n\t  ")
        self.assertIn("Пустой патч", str(ctx.exception))

    def test_check_file_integration(self):
        unique_id = uuid.uuid4().hex
        patch_file_path = os.path.join(self.repo_path, f"patch_{unique_id}.patch")
        patch_content = self._generate_diff()

        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(patch_content)

        checker = PatchChecker(repo_path=self.repo_path)
        result = checker.check_file(patch_file_path)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertIn("analysis", result)
        self.assertTrue(os.path.exists(patch_file_path))

    def test_check_file_not_found(self):
        missing_path = os.path.join(self.repo_path, f"non_existent_{uuid.uuid4().hex}.patch")
        checker = PatchChecker(repo_path=self.repo_path)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_file(missing_path)
        self.assertIn("Файл не найден", str(ctx.exception))

    def test_check_stream_integration(self):
        patch_content = self._generate_diff()
        stream = io.StringIO(patch_content)

        checker = PatchChecker(repo_path=self.repo_path)
        result = checker.check_stream(stream)

        self.assertIsInstance(result, dict)
        self.assertIn("is_safe", result)
        self.assertIn("evaluation", result)

    def test_check_method_and_policy(self):
        patch_content = self._generate_diff()
        policy = {
            "strict_safety": True,
            "disallow_syntax_risks": True
        }
        checker = PatchChecker(policy=policy)

        result = checker.check(patch_content, repo_path=self.repo_path)

        self.assertEqual(checker.repo_path, self.repo_path)
        self.assertIn("policy_verdict", result)
        self.assertIn("metrics", result)

    def test_standalone_check_patch_function(self):
        filename = f"target_{uuid.uuid4().hex[:6]}.py"
        patch_content = self._generate_diff(file_name=filename)

        result = check_patch(
            patch_content=patch_content,
            repo_path=self.repo_path,
            target_file=filename,
            policy={"strict_safety": False}
        )

        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)


if __name__ == "__main__":
    unittest.main()