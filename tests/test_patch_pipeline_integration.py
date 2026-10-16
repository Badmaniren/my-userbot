import unittest
import uuid
import random
from skills.patch_pipeline import PatchPipeline, PatchPipelineError
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector


class TestPatchPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = PatchPipeline()

    def test_process_patch_valid_and_sanitized(self):
        unique_var = f"var_{uuid.uuid4().hex[:8]}"
        unique_val = random.randint(1, 1000)
        raw_code = f"eval('__import__(\"os\")')\n{unique_var} = {unique_val}"

        result = self.pipeline.process_patch(raw_code)

        self.assertNotIn("eval", result)
        self.assertIn(unique_var, result)
        self.assertIn(str(unique_val), result)

    def test_process_patch_autocorrection_flow(self):
        unique_func = f"func_{uuid.uuid4().hex[:8]}"
        malformed_code = f"def {unique_func}():\n    print('test'"

        result = self.pipeline.process_patch(malformed_code)

        self.assertIn(unique_func, result)
        self.assertIn(")", result)

    def test_batch_process_integration(self):
        key1 = f"key_{uuid.uuid4().hex[:6]}"
        key2 = f"key_{uuid.uuid4().hex[:6]}"
        val1 = f"x = {random.randint(10, 50)}"
        val2 = f"y = {random.randint(51, 100)}"

        batch = {
            key1: val1,
            key2: val2
        }

        results = self.pipeline.batch_process(batch)

        self.assertIn(key1, results)
        self.assertIn(key2, results)
        self.assertIn(val1, results[key1])
        self.assertIn(val2, results[key2])

    def test_process_stream_integration(self):
        stream_data = f"x = {random.randint(100, 999)}\ny = x * 2"

        result = self.pipeline.process_stream(stream_data)

        self.assertIsInstance(result, str)
        self.assertIn("x =", result)


if __name__ == "__main__":
    unittest.main()