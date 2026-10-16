import unittest
import uuid
import random
import tempfile
import shutil
import os

from skills.patch_pipeline import PatchPipeline
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector


class TestPatchPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

        self.pipeline = PatchPipeline(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator,
            autocorrector=self.autocorrector
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_integration_flow(self):
        unique_id = str(uuid.uuid4())
        func_suffix = unique_id.replace("-", "_")
        random_value = random.randint(1000, 9999)

        malformed_code = f"""
def generated_func_{func_suffix}():
    x = {random_value}
    try:
        raise Exception("test")
    except:
        pass
    return x
"""

        result_code = self.pipeline.process(malformed_code)

        self.assertIsInstance(result_code, str)
        self.assertIn(str(func_suffix), result_code)
        self.assertIn(str(random_value), result_code)
        self.assertTrue(self.validator.validate_code(result_code))

    def test_pipeline_batch_integration(self):
        batch_id_1 = str(uuid.uuid4()).replace("-", "_")
        batch_id_2 = str(uuid.uuid4()).replace("-", "_")

        patches = {
            f"patch_{batch_id_1}.py": f"def func_a_{batch_id_1}():\n    return {random.randint(1, 100)}",
            f"patch_{batch_id_2}.py": f"def func_b_{batch_id_2}():\n    return {random.randint(101, 200)}"
        }

        pipeline_results = self.pipeline.batch_process(patches)

        self.assertIsInstance(pipeline_results, dict)
        self.assertIn(f"patch_{batch_id_1}.py", pipeline_results)
        self.assertIn(f"patch_{batch_id_2}.py", pipeline_results)

        for filename, processed_code in pipeline_results.items():
            self.assertIsInstance(processed_code, str)
            self.assertTrue(self.validator.validate_code(processed_code))


if __name__ == '__main__':
    unittest.main()