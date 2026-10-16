import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.patch_pipeline import PatchPipeline
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector

class TestPatchPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.pipeline = PatchPipeline(repo_path=self.repo_path)

    def test_pipeline_execution_flow(self):
        random_code = f"def {uuid.uuid4().hex}(): pass"
        sanitized_code = f"def {uuid.uuid4().hex}_sanitized(): pass"

        with patch('skills.code_sanitizer.CodeSanitizer.sanitize_patch') as mock_sanitize, \
             patch('skills.code_validator.CodeValidator.validate_code') as mock_validate, \
             patch('skills.patch_autocorrector.PatchAutocorrector.correct_and_validate') as mock_correct:

            mock_sanitize.return_value = sanitized_code
            mock_validate.return_value = True
            mock_correct.return_value = sanitized_code

            result = self.pipeline.process(random_code)

            self.assertEqual(result, sanitized_code)
            mock_sanitize.assert_called_once_with(random_code)
            mock_validate.assert_called_once_with(sanitized_code)

    def test_pipeline_validation_failure_triggers_autocorrector(self):
        malformed_code = f"class {uuid.uuid4().hex}: error_here"
        corrected_code = f"class {uuid.uuid4().hex}: fixed"

        with patch('skills.code_sanitizer.CodeSanitizer.sanitize_patch') as mock_sanitize, \
             patch('skills.code_validator.CodeValidator.validate_code') as mock_validate, \
             patch('skills.patch_autocorrector.PatchAutocorrector.correct_and_validate') as mock_correct:

            mock_sanitize.return_value = malformed_code
            mock_validate.return_value = False
            mock_correct.return_value = corrected_code

            result = self.pipeline.process(malformed_code)

            self.assertEqual(result, corrected_code)
            mock_correct.assert_called_once_with(malformed_code)

    def test_pipeline_stream_processing(self):
        random_stream_content = "".join(random.choices(string.ascii_letters, k=100))
        stream = io.StringIO(random_stream_content)

        with patch('skills.code_sanitizer.CodeSanitizer.sanitize_stream') as mock_sanitize_stream:
            expected_output = f"processed_{uuid.uuid4().hex}"
            mock_sanitize_stream.return_value = expected_output

            result = self.pipeline.process_stream(stream)

            self.assertEqual(result, expected_output)
            mock_sanitize_stream.assert_called_once()

    def test_pipeline_batch_processing(self):
        batch_size = random.randint(2, 10)
        patch_batch = {f"file_{uuid.uuid4().hex}": f"code_{uuid.uuid4().hex}" for _ in range(batch_size)}

        with patch('skills.code_sanitizer.CodeSanitizer.batch_sanitize') as mock_batch_sanitize:
            mock_batch_sanitize.return_value = patch_batch

            result = self.pipeline.process_batch(patch_batch)

            self.assertEqual(result, patch_batch)
            mock_batch_sanitize.assert_called_once_with(patch_batch)

    def test_pipeline_initialization_dependencies(self):
        self.assertIsInstance(self.pipeline.sanitizer, CodeSanitizer)
        self.assertIsInstance(self.pipeline.validator, CodeValidator)
        self.assertIsInstance(self.pipeline.autocorrector, PatchAutocorrector)
        self.assertEqual(self.pipeline.repo_path, self.repo_path)

if __name__ == '__main__':
    unittest.main()