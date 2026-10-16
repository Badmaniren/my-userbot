import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.patch_pipeline import PatchPipeline, PatchPipelineError

class TestPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.pipeline = PatchPipeline(repo_path=self.repo_path)

        self.random_str = str(uuid.uuid4())
        self.random_var = f"var_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_patch_valid_integration(self):
        valid_code = f"def foo_{self.random_str.replace('-', '_')}():\n    {self.random_var} = {random.randint(1, 100)}\n    return {self.random_var}"

        result = self.pipeline.process_patch(valid_code)
        self.assertIn(self.random_var, result)

    def test_process_patch_autocorrection_integration(self):
        val = random.randint(100, 999)
        malformed_code = f"def bar_{self.random_str.replace('-', '_')}():\n    eval('print({val})')"

        try:
            result = self.pipeline.process_patch(malformed_code)
            self.assertIsInstance(result, str)
        except PatchPipelineError as e:
            self.assertIn("Автокоррекция", str(e))

    def test_process_stream_integration(self):
        stream_content = f"x = {random.randint(1, 50)}\ny = {random.randint(51, 100)}\nresult_{self.random_var} = x + y"

        result = self.pipeline.process_stream(stream_content)
        self.assertIn(self.random_var, result)

    def test_batch_process_integration(self):
        batch_key = f"file_{uuid.uuid4().hex[:6]}.py"
        batch_code = f"z = {random.randint(1000, 9999)}"
        batch_data = {batch_key: batch_code}

        result = self.pipeline.batch_process(batch_data)
        self.assertIn(batch_key, result)
        self.assertEqual(result[batch_key], batch_code)

    def test_pipeline_error_handling_integration(self):
        invalid_syntax_code = f"def broken_func({self.random_var}"

        with self.assertRaises(PatchPipelineError):
            self.pipeline.process_patch(invalid_syntax_code)

if __name__ == '__main__':
    unittest.main()