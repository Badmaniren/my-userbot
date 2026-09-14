import unittest
from unittest.mock import patch, MagicMock
import io

from skills.error_pipeline import ErrorPipeline

class TestErrorPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = ErrorPipeline()

    def test_pipeline_composition_and_analysis_flow(self):
        with patch('skills.error_pipeline.ErrorAnalyzer') as MockAnalyzer, \
             patch('skills.error_pipeline.AutoCorrector') as MockCorrector:

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.parse_log.return_value = True
            analyzer_instance.analyze_and_prevent.return_value = True

            corrector_instance = MockCorrector.return_value
            corrector_instance.correct_code.return_value = True

            result = self.pipeline.run_pipeline("dummy_path.log")

            self.assertTrue(result)
            analyzer_instance.parse_log.assert_called_once_with("dummy_path.log")
            analyzer_instance.analyze_and_prevent.assert_called()
            corrector_instance.correct_code.assert_called()

    def test_pipeline_handles_analyzer_failure(self):
        with patch('skills.error_pipeline.ErrorAnalyzer') as MockAnalyzer, \
             patch('skills.error_pipeline.AutoCorrector') as MockCorrector:

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.parse_log.return_value = False

            result = self.pipeline.run_pipeline("bad_path.log")

            self.assertFalse(result)

    def test_pipeline_stream_processing_with_io_bytes(self):
        with patch('skills.error_pipeline.ErrorAnalyzer') as MockAnalyzer, \
             patch('skills.error_pipeline.AutoCorrector') as MockCorrector:

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.process_stream.return_value = True

            corrector_instance = MockCorrector.return_value
            corrector_instance.process_error_stream.return_value = True

            stream_mock = io.BytesIO(b"CRITICAL ERROR 500")

            result = self.pipeline.process_stream_pipeline(stream_mock)

            self.assertTrue(result)
            analyzer_instance.process_stream.assert_called_once()
            corrector_instance.process_error_stream.assert_called_once()

    def test_pipeline_raises_exception_properly(self):
        with patch('skills.error_pipeline.ErrorAnalyzer') as MockAnalyzer:
            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.parse_log.side_effect = RuntimeError("System Failure")

            with self.assertRaises(RuntimeError):
                self.pipeline.run_pipeline("fatal.log")

    def test_pipeline_web_verification_step(self):
        with patch('skills.error_pipeline.AutoCorrector') as MockCorrector:
            corrector_instance = MockCorrector.return_value
            corrector_instance.verify_fix_via_web.return_value = True

            result = self.pipeline.verify_pipeline_fix("http://localhost/health")

            self.assertTrue(result)
            corrector_instance.verify_fix_via_web.assert_called_once_with("http://localhost/health")

    def test_pipeline_returns_false_on_correction_failure(self):
        with patch('skills.error_pipeline.ErrorAnalyzer') as MockAnalyzer, \
             patch('skills.error_pipeline.AutoCorrector') as MockCorrector:

            analyzer_instance = MockAnalyzer.return_value
            analyzer_instance.parse_log.return_value = True
            analyzer_instance.analyze_and_prevent.return_value = True

            corrector_instance = MockCorrector.return_value
            corrector_instance.correct_code.return_value = False

            result = self.pipeline.run_pipeline("error.log")

            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()