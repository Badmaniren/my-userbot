import unittest
from unittest.mock import patch
import io
from skills.error_pipeline import ErrorPipeline

class TestErrorPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = ErrorPipeline()

    def test_run_pipeline_success(self):
        log_path = "dummy_path.log"
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=True) as mock_parse, \
             patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.correct_code', return_value=True) as mock_correct:
            
            result = self.pipeline.run_pipeline(log_path)
            self.assertTrue(result)
            mock_parse.assert_called_once_with(log_path)
            mock_analyze.assert_called_once_with(log_path)
            mock_correct.assert_called_once_with(log_path)

    def test_run_pipeline_parse_empty(self):
        log_path = "dummy_path.log"
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=False) as mock_parse, \
             patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent') as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.correct_code') as mock_correct:
            
            result = self.pipeline.run_pipeline(log_path)
            self.assertFalse(result)
            mock_parse.assert_called_once_with(log_path)
            mock_analyze.assert_not_called()
            mock_correct.assert_not_called()

    def test_run_pipeline_parse_raises(self):
        log_path = "dummy_path.log"
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', side_effect=Exception("Parse error")):
            with self.assertRaises(Exception):
                self.pipeline.run_pipeline(log_path)

    def test_run_pipeline_analyze_false(self):
        log_path = "dummy_path.log"
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=True), \
             patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=False), \
             patch('skills.auto_corrector.AutoCorrector.correct_code') as mock_correct:
            
            result = self.pipeline.run_pipeline(log_path)
            self.assertFalse(result)
            mock_correct.assert_not_called()

    def test_process_stream_pipeline_success(self):
        stream = io.BytesIO(b'stream data')
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', return_value=True), \
             patch('skills.auto_corrector.AutoCorrector.process_error_stream', return_value=True):
            
            result = self.pipeline.process_stream_pipeline(stream)
            self.assertTrue(result)

    def test_process_stream_pipeline_failure(self):
        stream = io.BytesIO(b'stream data')
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', return_value=True), \
             patch('skills.auto_corrector.AutoCorrector.process_error_stream', return_value=False):
            
            result = self.pipeline.process_stream_pipeline(stream)
            self.assertFalse(result)

    def test_verify_pipeline_fix_success(self):
        url = "http://example.com/health"
        with patch('skills.auto_corrector.AutoCorrector.verify_fix_via_web', return_value=True):
            result = self.pipeline.verify_pipeline_fix(url)
            self.assertTrue(result)

    def test_verify_pipeline_fix_failure(self):
        url = "http://example.com/health"
        with patch('skills.auto_corrector.AutoCorrector.verify_fix_via_web', return_value=False):
            result = self.pipeline.verify_pipeline_fix(url)
            self.assertFalse(result)

    def test_process_error_stream_success(self):
        signature = "ERR_CODE_001"
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True), \
             patch('skills.auto_corrector.AutoCorrector.correct_code', return_value=True):
            
            result = self.pipeline.process_error_stream(signature)
            self.assertTrue(result)

    def test_process_error_stream_failure(self):
        signature = "ERR_CODE_001"
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True), \
             patch('skills.auto_corrector.AutoCorrector.correct_code', return_value=False):
            
            result = self.pipeline.process_error_stream(signature)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()