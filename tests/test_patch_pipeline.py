import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.patch_pipeline import PatchPipeline, PatchPipelineError

class TestPatchPipelineInquisitor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_content = ''.join(random.choices(string.ascii_letters + string.whitespace, k=64))
        self.pipeline = PatchPipeline(repo_path=self.repo_path)

    def test_pipeline_initialization_random(self):
        rand_path = f"/var/repo/{uuid.uuid4().hex}"
        pipeline_inst = PatchPipeline(repo_path=rand_path)
        self.assertEqual(pipeline_inst.repo_path, rand_path)

    @patch('skills.patch_pipeline.code_validator')
    @patch('skills.patch_pipeline.patch_analyzer')
    @patch('skills.patch_pipeline.patch_autocorrector')
    def test_process_patch_success_flow(self, mock_autocorrector, mock_analyzer, mock_validator):
        mock_validator.validate.return_value = True
        mock_analyzer.analyze.return_value = {"status": "ok", "hash": uuid.uuid4().hex}
        mock_autocorrector.apply_fixes.return_value = True

        result = self.pipeline.process(self.patch_content)

        self.assertTrue(result)
        mock_validator.validate.assert_called_once_with(self.patch_content)
        mock_analyzer.analyze.assert_called_once_with(self.patch_content)
        mock_autocorrector.apply_fixes.assert_called_once()

    @patch('skills.patch_pipeline.code_validator')
    def test_process_patch_validation_failure(self, mock_validator):
        err_msg = uuid.uuid4().hex
        mock_validator.validate.side_effect = Exception(err_msg)

        with self.assertRaises(PatchPipelineError) as ctx:
            self.pipeline.process(self.patch_content)

        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_pipeline.code_validator')
    @patch('skills.patch_pipeline.patch_analyzer')
    def test_process_patch_analysis_failure(self, mock_analyzer, mock_validator):
        mock_validator.validate.return_value = True
        analysis_error = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = RuntimeError(analysis_error)

        with self.assertRaises(PatchPipelineError) as ctx:
            self.pipeline.process(self.patch_content)

        self.assertIn(analysis_error, str(ctx.exception))

    @patch('skills.patch_pipeline.code_validator')
    @patch('skills.patch_pipeline.patch_analyzer')
    @patch('skills.patch_pipeline.patch_autocorrector')
    @patch('skills.patch_pipeline.git_inspector')
    def test_integrity_control_rollback_on_failure(self, mock_inspector, mock_autocorrector, mock_analyzer, mock_validator):
        mock_validator.validate.return_value = True
        mock_analyzer.analyze.return_value = {"status": "warning"}
        mock_autocorrector.apply_fixes.side_effect = ValueError(uuid.uuid4().hex)

        rollback_mock = MagicMock()
        self.pipeline.rollback_controller = rollback_mock

        with self.assertRaises(PatchPipelineError):
            self.pipeline.process(self.patch_content)

        rollback_mock.execute_rollback.assert_called_once()

    def test_stream_patch_processing_with_io(self):
        random_bytes = uuid.uuid4().bytes + b'\x00\xff'
        stream = io.BytesIO(random_bytes)

        with patch('skills.patch_pipeline.code_validator') as mock_val:
            mock_val.validate_stream.return_value = True
            res = self.pipeline.process_stream(stream)
            self.assertTrue(res)
            mock_val.validate_stream.assert_called_once_with(stream)

if __name__ == '__main__':
    unittest.main()