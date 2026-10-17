import unittest
import uuid
import random
import os
import tempfile
from skills.patch_checker import PatchChecker
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult

class TestPatchCheckerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patch_analyzer = PatchAnalyzer()
        self.patch_evaluator = PatchEvaluator(repo_path=self.test_dir)
        self.patch_checker = PatchChecker()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_patch_checker_integration_workflow(self):
        random_id = str(uuid.uuid4())
        random_lines_count = random.randint(5, 20)
        
        diff_lines = [
            f"diff --git a/file_{random_id}.py b/file_{random_id}.py",
            "index 1234567..89abcdef 100644",
            f"--- a/file_{random_id}.py",
            f"+++ b/file_{random_id}.py",
            "@@ -0,0 +1,1 @@",
            f"+print('Integration test {random_id}')"
        ]
        
        for i in range(random_lines_count):
            diff_lines.append(f"+# random line {random.randint(1000, 9999)}")
            
        diff_text = "\n".join(diff_lines)

        analysis_result = self.patch_analyzer.analyze(diff_text)
        self.assertIsNotNone(analysis_result, "PatchAnalyzer не должен возвращать None")

        evaluation_result = self.patch_evaluator.evaluate(patch_content=diff_text, collect_telemetry=True)
        self.assertIsInstance(evaluation_result, PatchEvaluationResult)

        checker_result = self.patch_checker.check(patch_content=diff_text, repo_path=self.test_dir)
        
        self.assertIn("is_safe", checker_result)
        self.assertIn("metrics", checker_result)
        self.assertEqual(evaluation_result.is_safe, checker_result["is_safe"])
        
        expected_marker = f"Integration test {random_id}"
        self.assertIn(expected_marker, diff_text)

if __name__ == "__main__":
    unittest.main()