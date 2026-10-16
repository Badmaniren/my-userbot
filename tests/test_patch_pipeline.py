import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import ast

from skills.patch_pipeline import PatchPipeline, PatchPipelineError
from skills.code_sanitizer import CodeSanitizerError
from skills.code_validator import CodeValidatorError, CodeValidatorASTError
from skills.patch_autocorrector import PatchAutocorrectorError

class TestPatchPipelineInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.pipeline = PatchPipeline(repo_path=self.repo_path)

    def test_process_patch_success_direct(self):
        rand_var = f"var_{uuid.uuid4().hex[:8]}"
        valid_code = f"{rand_var} = {random.randint(1, 100)}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_patch', return_value=valid_code) as mock_sanitize, \
             patch.object(self.pipeline.validator, 'validate_code', return_value=True) as mock_validate:

            result = self.pipeline.process_patch(valid_code)
            self.assertEqual(result, valid_code)
            mock_sanitize.assert_called_once_with(valid_code)
            mock_validate.assert_called_once_with(valid_code)

    def test_process_patch_sanitizer_error(self):
        rand_err_msg = f"err_{uuid.uuid4().hex}"
        dirty_code = f"bad_code_{uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_patch', side_effect=CodeSanitizerError(rand_err_msg)):
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.process_patch(dirty_code)
            self.assertIn(rand_err_msg, str(ctx.exception))

    def test_process_patch_validation_fails_triggers_autocorrect(self):
        rand_malformed = f"malformed_{uuid.uuid4().hex}"
        rand_fixed = f"fixed_{uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_patch', return_value=rand_malformed), \
             patch.object(self.pipeline.validator, 'validate_code', side_effect=CodeValidatorError(f"syntax fail {uuid.uuid4().hex}")), \
             patch.object(self.pipeline.autocorrector, 'correct_and_validate', return_value=rand_fixed) as mock_correct:

            result = self.pipeline.process_patch(rand_malformed)
            self.assertEqual(result, rand_fixed)
            mock_correct.assert_called_once_with(rand_malformed)

    def test_process_patch_autocorrect_fails(self):
        rand_malformed = f"malformed_{uuid.uuid4().hex}"
        rand_err = f"autocorrect error {uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_patch', return_value=rand_malformed), \
             patch.object(self.pipeline.validator, 'validate_code', side_effect=CodeValidatorError("fail")), \
             patch.object(self.pipeline.autocorrector, 'correct_and_validate', side_effect=PatchAutocorrectorError(rand_err)):

            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.process_patch(rand_malformed)
            self.assertIn(rand_err, str(ctx.exception))

    def test_process_stream_success(self):
        rand_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)
        rand_sanitized = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_stream', return_value=rand_sanitized) as mock_sanitize, \
             patch.object(self.pipeline.validator, 'validate_stream', return_value=True) as mock_validate:

            result = self.pipeline.process_stream(mock_stream)
            self.assertEqual(result, rand_sanitized)
            mock_sanitize.assert_called_once_with(mock_stream)
            mock_validate.assert_called_once_with(rand_sanitized)

    def test_process_stream_sanitizer_error(self):
        mock_stream = io.BytesIO(b"some bytes")
        rand_err = f"stream sanitize error {uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_stream', side_effect=CodeSanitizerError(rand_err)):
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.process_stream(mock_stream)
            self.assertIn(rand_err, str(ctx.exception))

    def test_process_stream_validator_error(self):
        mock_stream = io.BytesIO(b"some bytes")
        rand_err = f"stream validation error {uuid.uuid4().hex}"
        rand_sanitized = f"sanitized_{uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'sanitize_stream', return_value=rand_sanitized), \
             patch.object(self.pipeline.validator, 'validate_stream', side_effect=CodeValidatorError(rand_err)):

            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.process_stream(mock_stream)
            self.assertIn(rand_err, str(ctx.exception))

    def test_batch_process_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = f"val_{uuid.uuid4().hex}"
        batch_data = {rand_key: rand_val}
        rand_sanitized_batch = {rand_key: f"sanitized_{rand_val}"}

        with patch.object(self.pipeline.sanitizer, 'batch_sanitize', return_value=rand_sanitized_batch) as mock_batch_sanitize, \
             patch.object(self.pipeline.validator, 'batch_validate', return_value=True) as mock_batch_validate:

            result = self.pipeline.batch_process(batch_data)
            self.assertEqual(result, rand_sanitized_batch)
            mock_batch_sanitize.assert_called_once_with(batch_data)
            mock_batch_validate.assert_called_once_with(rand_sanitized_batch)

    def test_batch_process_sanitizer_error(self):
        batch_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_err = f"batch sanitize error {uuid.uuid4().hex}"

        with patch.object(self.pipeline.sanitizer, 'batch_sanitize', side_effect=CodeSanitizerError(rand_err)):
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.batch_process(batch_data)
            self.assertIn(rand_err, str(ctx.exception))

    def test_batch_process_validator_error(self):
        batch_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_err = f"batch validator error {uuid.uuid4().hex}"
        rand_sanitized = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.pipeline.sanitizer, 'batch_sanitize', return_value=rand_sanitized), \
             patch.object(self.pipeline.validator, 'batch_validate', side_effect=CodeValidatorError(rand_err)):

            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.batch_process(batch_data)
            self.assertIn(rand_err, str(ctx.exception))