import unittest
from unittest.mock import patch, MagicMock
import io
from skills.error_pipeline import ErrorPipeline

class TestErrorPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = ErrorPipeline()

    def test_pipeline_composition_and_analysis_flow(self):
        with patch.object(self.pipeline.analyzer, 'parse_log', return_value=True) as mock_parse, \
             patch.object(self.pipeline.analyzer, 'analyze_and_prevent', return_value=True) as mock_analyze, \
             patch.object(self.pipeline.corrector, 'correct_code', return_value=True) as mock_correct:
            
            result = self.pipeline.run_pipeline("dummy_path.log")
            self.assertTrue(result)
            mock_parse.assert_called_once_with("dummy_path.log")
            mock_analyze.assert_called_once_with("dummy_path.log")
            mock_correct.assert_called_once_with("dummy_path.log")

    def test_pipeline_handles_analyzer_failure(self):
        with patch.object(self.pipeline.analyzer, 'parse_log', return_value=False) as mock_parse, \
             patch.object(self.pipeline.analyzer, 'analyze_and_prevent') as mock_analyze:
            
            result = self.pipeline.run_pipeline("bad_path.log")
            self.assertFalse(result)
            mock_parse.assert_called_once_with("bad_path.log")
            mock_analyze.assert_not_called()

    def test_pipeline_raises_exception_properly(self):
        with patch.object(self.pipeline.analyzer, 'parse_log', side_effect=Exception("Fatal Error")) as mock_parse:
            with self.assertRaises(Exception):
                self.pipeline.run_pipeline("fatal.log")
            mock_parse.assert_called_once_with("fatal.log")

    def test_pipeline_returns_false_on_correction_failure(self):
        with patch.object(self.pipeline.analyzer, 'parse_log', return_value=True), \
             patch.object(self.pipeline.analyzer, 'analyze_and_prevent', return_value=True), \
             patch.object(self.pipeline.corrector, 'correct_code', return_value=False):
            
            result = self.pipeline.run_pipeline("fail_correct.log")
            self.assertFalse(result)

    def test_process_stream_pipeline(self):
        mock_stream = io.BytesIO(b'stream data')
        with patch.object(self.pipeline.analyzer, 'process_stream', return_value=True) as mock_proc_analyzer, \
             patch.object(self.pipeline.corrector, 'process_error_stream', return_value=True) as mock_proc_corrector:
            
            result = self.pipeline.process_stream_pipeline(mock_stream)
            self.assertTrue(result)
            mock_proc_analyzer.assert_called_once_with(mock_stream)
            mock_proc_corrector.assert_called_once_with(mock_stream)

    def test_verify_pipeline_fix(self):
        url = "http://example.com/fix"
        with patch.object(self.pipeline.corrector, 'verify_fix_via_web', return_value=True) as mock_verify:
            result = self.pipeline.verify_pipeline_fix(url)
            self.assertTrue(result)
            mock_verify.assert_called_once_with(url)

    def test_process_error_stream_method(self):
        signature = "ValueError: test error"
        with patch.object(self.pipeline.analyzer, 'analyze_and_prevent', return_value=True) as mock_analyze, \
             patch.object(self.pipeline.corrector, 'correct_code', return_value=True) as mock_correct:
            
            result = self.pipeline.process_error_stream(signature)
            self.assertTrue(result)
            mock_analyze.assert_called_once_with(signature)
            mock_correct.assert_called_once_with(signature)

if __name__ == '__main__':
    unittest.main()