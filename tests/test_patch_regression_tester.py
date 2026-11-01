import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.patch_regression_tester import start_new


class TestPatchRegressionTesterStartNew(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = uuid.uuid4().hex
        self.rand_str_2 = uuid.uuid4().hex
        self.rand_int = random.randint(100, 99999)
        self.rand_float = random.random() * 100
        self.test_data = {
            "patch_id": self.rand_str_1,
            "target_branch": self.rand_str_2,
            "timeout": self.rand_int,
            "tolerance": self.rand_float
        }

    def test_start_new_success_execution(self):
        with patch("skills.patch_regression_tester.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_regression_tester.GitInspector") as mock_git_cls:
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            expected_result = {
                "status": "stable",
                "verified_patch": self.rand_str_1,
                "score": self.rand_float
            }
            mock_evaluator_instance.evaluate.return_value = expected_result

            mock_git_instance = mock_git_cls.return_value
            mock_git_instance.analyze_repository.return_value = True

            result = start_new(self.test_data)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("verified_patch"), self.rand_str_1)
            self.assertEqual(result.get("status"), "stable")

    def test_start_new_handles_malformed_input(self):
        corrupted_data = {
            "".join(random.choices(string.ascii_lowercase, k=8)): uuid.uuid4().hex
            for _ in range(5)
        }
        
        with patch("skills.patch_regression_tester.PatchEvaluator") as mock_evaluator_cls:
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.side_effect = KeyError(self.rand_str_1)

            with self.assertRaises((KeyError, ValueError, TypeError)):
                start_new(corrupted_data)

    def test_start_new_io_integration_stream(self):
        stream_data = io.BytesIO(f"test_payload_{self.rand_str_2}".encode('utf-8'))
        
        with patch("skills.patch_regression_tester.PatchSanitizer") as mock_sanitizer:
            mock_sanitizer_instance = mock_sanitizer.return_value
            mock_sanitizer_instance.sanitize_stream.return_value = stream_data

            enriched_data = {
                **self.test_data,
                "stream_ref": stream_data
            }

            result = start_new(enriched_data)

            self.assertIsNotNone(result)
            mock_sanitizer_instance.sanitize_stream.assert_called_once()

    def test_start_new_regression_failure_handling(self):
        fail_reason = f"regression_detected_{uuid.uuid4().hex}"
        
        with patch("skills.patch_regression_tester.PatchEvaluator") as mock_evaluator_cls:
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.return_value = {
                "status": "unstable",
                "reason": fail_reason,
                "patch_id": self.rand_str_1
            }

            result = start_new(self.test_data)

            self.assertEqual(result.get("status"), "unstable")
            self.assertEqual(result.get("reason"), fail_reason)


if __name__ == "__main__":
    unittest.main()