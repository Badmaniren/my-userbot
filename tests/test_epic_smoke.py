import unittest
import tempfile
import os

from patch_sanitizer import patch_sanitizer
from patch_checker import patch_checker
from patch_analyzer import patch_analyzer
from patch_evaluator import patch_evaluator
from patch_verifier import patch_verifier
from patch_applier import patch_applier

class TestPatchPipelineEpicPracticalCheck(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.test_dir.name, "target_module.py")
        
        original_code = (
            "def calculate_sum(a, b):\n"
            "    # TODO: implement sum\n"
            "    return 0\n"
        )
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(original_code)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_safe_patch_pipeline_end_to_end(self):
        raw_patch = (
            f"--- {self.test_file_path}\n"
            f"+++ {self.test_file_path}\n"
            "@@ -1,3 +1,3 @@\n"
            " def calculate_sum(a, b):\n"
            "-    return 0\n"
            "+    return a + b\n"
        )

        print("\n[STEP 1] Sanitizing raw patch...")
        sanitized = patch_sanitizer.sanitize(raw_patch)
        print(f"Sanitized patch result length: {len(sanitized)} chars")
        self.assertTrue(len(sanitized) > 0)

        print("\n[STEP 2] Analyzing patch structure...")
        analysis = patch_analyzer.analyze(sanitized)
        print(f"Patch analysis result: {analysis}")
        self.assertIsNotNone(analysis)

        print("\n[STEP 3] Checking patch validity...")
        is_checked = patch_checker.check(sanitized)
        print(f"Patch check status: {is_checked}")
        self.assertTrue(is_checked)

        print("\n[STEP 4] Evaluating patch safety and metrics...")
        evaluation = patch_evaluator.evaluate(sanitized)
        print(f"Patch evaluation score/status: {evaluation}")
        self.assertIsNotNone(evaluation)

        print("\n[STEP 5] Final verification before application...")
        is_verified = patch_verifier.verify(sanitized)
        print(f"Patch verification status: {is_verified}")
        self.assertTrue(is_verified)

        print("\n[STEP 6] Applying patch to target repository/file...")
        applied_status = patch_applier.apply(sanitized)
        print(f"Patch apply status: {applied_status}")
        self.assertTrue(applied_status)

        with open(self.test_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        print("\n[RESULT] Final file content after successful pipeline execution:")
        print("----------------------------------------")
        print(updated_content.strip())
        print("----------------------------------------")

        self.assertIn("return a + b", updated_content)

if __name__ == "__main__":
    unittest.main()