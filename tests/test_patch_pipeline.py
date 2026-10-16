import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.patch_pipeline import PatchPipeline, PatchPipelineError
from skills.code_sanitizer import CodeSanitizerError
from skills.patch_autocorrector import PatchAutocorrectorError

class TestPatchPipeline(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.mock_sanitizer = MagicMock()
        self.mock_validator = MagicMock()
        self.mock_autocorrector = MagicMock()
        self.pipeline = PatchPipeline(
            repo_path=self.repo_path,
            sanitizer=self.mock_sanitizer,
            validator=self.mock_validator,
            autocorrector=self.mock_autocorrector
        )

    def test_process_patch_success_first_try(self):
        raw_code = f"def {uuid.uuid4().hex}(): pass"
        sanitized = f"def {uuid.uuid4().hex}(): pass"

        self.mock_sanitizer.sanitize_patch.return_value = sanitized
        self.mock_validator.validate_code.return_value = True

        result = self.pipeline.process_patch(raw_code)

        self.assertEqual(result, sanitized)
        self.mock_sanitizer.sanitize_patch.assert_called_once_with(raw_code)
        self.mock_validator.validate_code.assert_called_once_with(sanitized)

    def test_process_patch_autocorrection_flow(self):
        raw_code = f"bad_code = {random.randint(1, 100)}"
        sanitized = f"good_code = {random.randint(101, 200)}"
        corrected = f"fixed_code = {random.randint(201, 300)}"

        self.mock_sanitizer.sanitize_patch.return_value = sanitized
        self.mock_validator.validate_code.return_value = False
        self.mock_autocorrector.correct_and_validate.return_value = corrected

        result = self.pipeline.process_patch(raw_code)

        self.assertEqual(result, corrected)
        self.mock_autocorrector.correct_and_validate.assert_called_once_with(sanitized)

    def test_process_patch_sanitizer_error(self):
        raw_code = uuid.uuid4().hex
        error_msg = uuid.uuid4().hex
        self.mock_sanitizer.sanitize_patch.side_effect = CodeSanitizerError(error_msg)
        self.mock_autocorrector.correct_and_validate.side_effect = PatchAutocorrectorError(error_msg)

        with self.assertRaises(PatchPipelineError) as cm:
            self.pipeline.process_patch(raw_code)
        self.assertIn(error_msg, str(cm.exception))

    def test_process_patch_autocorrector_error(self):
        raw_code = uuid.uuid4().hex
        error_msg = uuid.uuid4().hex
        self.mock_sanitizer.sanitize_patch.return_value = raw_code
        self.mock_validator.validate_code.return_value = False
        self.mock_autocorrector.correct_and_validate.side_effect = PatchAutocorrectorError(error_msg)

        with self.assertRaises(PatchPipelineError) as cm:
            self.pipeline.process_patch(raw_code)
        self.assertIn(error_msg, str(cm.exception))

    def test_process_stream(self):
        stream_content = f"stream_{uuid.uuid4().hex}".encode()
        stream = io.BytesIO(stream_content)
        sanitized = f"sanitized_{uuid.uuid4().hex}"
        transformed = f"transformed_{uuid.uuid4().hex}"

        self.mock_sanitizer.sanitize_stream.return_value = sanitized
        self.mock_validator.validate_stream.return_value = False
        self.mock_autocorrector.transform_stream.return_value = transformed

        result = self.pipeline.process_stream(stream)

        self.assertEqual(result, transformed)
        self.mock_sanitizer.sanitize_stream.assert_called_once()

    def test_batch_process(self):
        batch = {
            uuid.uuid4().hex: f"code_{uuid.uuid4().hex}",
            uuid.uuid4().hex: f"code_{uuid.uuid4().hex}"
        }

        with patch.object(self.pipeline, 'process_patch') as mock_process:
            mock_process.side_effect = lambda x: f"processed_{x}"
            result = self.pipeline.batch_process(batch)

            for k, v in batch.items():
                self.assertEqual(result[k], f"processed_{v}")
            self.assertEqual(mock_process.call_count, len(batch))

if __name__ == '__main__':
    unittest.main()