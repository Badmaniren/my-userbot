import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
import tempfile

from skills.patch_integrator import PatchIntegrator, PatchIntegratorError
from skills.code_validator import CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrectorError


class TestPatchIntegrator(unittest.TestCase):

    def setUp(self):
        self.repo_path = tempfile.mkdtemp()
        self.integrator = PatchIntegrator(repo_path=self.repo_path)
        self.random_file_path = f"{uuid.uuid4().hex}.py"
        self.random_code = f"def {uuid.uuid4().hex}_func():\n    return {random.randint(1, 100)}"

    def test_init_sets_components(self):
        self.assertIsNotNone(self.integrator.validator)
        self.assertIsNotNone(self.integrator.autocorrector)

    def test_integrate_patch_success(self):
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', return_value=self.random_code) as mock_correct, \
             patch.object(self.integrator.validator, 'validate_code', return_value=True) as mock_validate:

            result = self.integrator.integrate_patch(self.random_file_path, self.random_code)

            self.assertTrue(result)
            mock_correct.assert_called_once_with(self.random_code)
            mock_validate.assert_called_once_with(self.random_code)

    def test_integrate_patch_autocorrector_error(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', side_effect=PatchAutocorrectorError(err_msg)) as mock_correct:

            with self.assertRaises(PatchIntegratorError) as ctx:
                self.integrator.integrate_patch(self.random_file_path, self.random_code)

            self.assertIn(err_msg, str(ctx.exception))
            mock_correct.assert_called_once_with(self.random_code)

    def test_integrate_patch_generic_exception(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', side_effect=Exception(err_msg)) as mock_correct:

            with self.assertRaises(PatchIntegratorError) as ctx:
                self.integrator.integrate_patch(self.random_file_path, self.random_code)

            self.assertIn(err_msg, str(ctx.exception))
            mock_correct.assert_called_once_with(self.random_code)

    def test_integrate_patch_validation_failed(self):
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', return_value=self.random_code), \
             patch.object(self.integrator.validator, 'validate_code', return_value=False):

            with self.assertRaises(PatchIntegratorError) as ctx:
                self.integrator.integrate_patch(self.random_file_path, self.random_code)

            self.assertIn("Code validation failed after correction.", str(ctx.exception))

    def test_integrate_stream_success(self):
        stream_content = io.BytesIO(self.random_code.encode('utf-8'))
        transformed_code = f"# {uuid.uuid4().hex}\n" + self.random_code

        with patch.object(self.integrator.autocorrector, 'transform_stream', return_value=transformed_code) as mock_transform, \
             patch.object(self.integrator.validator, 'validate_stream', return_value=True) as mock_validate:

            result = self.integrator.integrate_stream(stream_content)

            self.assertTrue(result)
            mock_transform.assert_called_once_with(stream_content)
            mock_validate.assert_called_once_with(transformed_code)

    def test_batch_integrate_success(self):
        key1 = uuid.uuid4().hex
        key2 = uuid.uuid4().hex
        val1 = f"val_{uuid.uuid4().hex}"
        val2 = f"val_{uuid.uuid4().hex}"

        input_dict = {key1: val1, key2: val2}
        corrected_dict = {key1: val1 + "_c", key2: val2 + "_c"}
        validation_results = {key1: True, key2: False}

        with patch.object(self.integrator.autocorrector, 'batch_correct', return_value=corrected_dict) as mock_batch_correct, \
             patch.object(self.integrator.validator, 'batch_validate', return_value=validation_results) as mock_batch_validate:

            res = self.integrator.batch_integrate(input_dict)

            self.assertEqual(res, validation_results)
            mock_batch_correct.assert_called_once_with(input_dict)
            mock_batch_validate.assert_called_once_with(corrected_dict)

    def test_process_patch_success_writes_file(self):
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', return_value=self.random_code), \
             patch.object(self.integrator.validator, 'validate_code', return_value=True):

            result = self.integrator.process_patch(self.random_file_path, self.random_code)

            self.assertTrue(result)
            full_path = os.path.join(self.repo_path, self.random_file_path)
            self.assertTrue(os.path.exists(full_path))
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, self.random_code)

    def test_process_patch_autocorrector_exception(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', side_effect=Exception(err_msg)):
            with self.assertRaises(PatchIntegratorError) as ctx:
                self.integrator.process_patch(self.random_file_path, self.random_code)
            self.assertIn(err_msg, str(ctx.exception))

    def test_process_patch_validation_fails(self):
        with patch.object(self.integrator.autocorrector, 'correct_and_validate', return_value=self.random_code), \
             patch.object(self.integrator.validator, 'validate_code', return_value=False):
            with self.assertRaises(PatchIntegratorError) as ctx:
                self.integrator.process_patch(self.random_file_path, self.random_code)
            self.assertIn("Validation failed", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()