import unittest
import uuid
import random
import io
import tempfile
import os

from skills.patch_regression_tester import start_new, PatchRegressionTester
from skills.patch_sanitizer import PatchSanitizer
from skills.git_inspector import GitInspector
from skills.patch_evaluator import PatchEvaluator

class TestPatchRegressionTesterIntegration(unittest.TestCase):
    def test_patch_regression_flow_integration(self):
        unique_patch_id = f"patch-{uuid.uuid4()}"
        tolerance_value = round(random.uniform(0.1, 0.9), 2)
        
        test_data = {
            "patch_id": unique_patch_id,
            "tolerance": tolerance_value,
            "stream_ref": io.BytesIO(b"test patch stream data")
        }

        sanitizer = PatchSanitizer()
        self.assertIsNotNone(sanitizer)

        git_inspector = GitInspector()
        self.assertIsNotNone(git_inspector)

        evaluator = PatchEvaluator()
        self.assertIsNotNone(evaluator)

        tester_instance = PatchRegressionTester()
        self.assertIsInstance(tester_instance, PatchRegressionTester)

        result = start_new(test_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "stable")
        self.assertEqual(result.get("verified_patch"), unique_patch_id)
        self.assertEqual(result.get("score"), tolerance_value)

    def test_patch_regression_invalid_input(self):
        with self.assertRaises(TypeError):
            start_new("not_a_dictionary")

if __name__ == "__main__":
    unittest.main()