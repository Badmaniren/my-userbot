import unittest
import tempfile
import os
import shutil
import uuid
import random

from skills.patch_integrator import PatchIntegrator, PatchIntegratorError
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector


class TestPatchIntegratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.integrator = PatchIntegrator(repo_path=self.test_dir)

        self.unique_id = uuid.uuid4().hex
        self.var_name = f"var_{random.randint(1000, 9999)}_{self.unique_id[:6]}"
        self.func_name = f"func_{random.randint(1000, 9999)}_{self.unique_id[:6]}"

        self.valid_code = f"def {self.func_name}():\n    {self.var_name} = {random.randint(1, 100)}\n    return {self.var_name}\n"
        self.invalid_code = f"def {self.func_name}():\n    return {self.var_name}  # syntax or unbound error or malformed"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_patch_integration_success(self):
        file_path = f"modules/{self.unique_id}.py"

        result = self.integrator.process_patch(file_path, self.valid_code)
        self.assertTrue(result)

        full_path = os.path.join(self.test_dir, file_path)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.func_name, content)
        self.assertIn(self.var_name, content)

    def test_integrate_patch_failure_raises_error(self):
        file_path = f"modules/fail_{self.unique_id}.py"
        malformed_code = "def broken_syntax_def_123 456:"

        with self.assertRaises(PatchIntegratorError):
            self.integrator.integrate_patch(file_path, malformed_code)

    def test_batch_integrate_integration(self):
        file_1 = f"batch_a_{self.unique_id}.py"
        file_2 = f"batch_b_{self.unique_id}.py"

        func_1 = f"f1_{random.randint(100, 999)}"
        func_2 = f"f2_{random.randint(100, 999)}"

        patches = {
            file_1: f"def {func_1}():\n    pass\n",
            file_2: f"def {func_2}():\n    return {random.randint(10, 99)}\n"
        }

        results = self.integrator.batch_integrate(patches)
        self.assertIsInstance(results, dict)
        self.assertIn(file_1, results)
        self.assertIn(file_2, results)

    def test_integrate_stream_integration(self):
        stream_code = f"x_stream_{self.unique_id} = {random.randint(50, 500)}\n"
        res = self.integrator.integrate_stream(stream_code)
        self.assertIsInstance(res, bool)


if __name__ == "__main__":
    unittest.main()