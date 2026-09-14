import unittest
from unittest.mock import patch, MagicMock
from skills.error_pipeline import ErrorPipeline


class TestErrorPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = ErrorPipeline()

    def test_process_error_stream_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', return_value=True) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.process_error_stream', return_value=True) as mock_correct:
            result = self.pipeline.process_error_stream("stream_data")
            self.assertTrue(result)
            mock_analyze.assert_called_once_with("stream_data")
            mock_correct.assert_called_once_with("stream_data")

    def test_process_error_stream_analysis_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', return_value=False) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.process_error_stream', return_value=True) as mock_correct:
            result = self.pipeline.process_error_stream("stream_data")
            self.assertFalse(result)
            mock_analyze.assert_called_once_with("stream_data")
            mock_correct.assert_not_called()

    def test_parse_and_correct_log_file_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=True) as mock_parse, \
             patch('skills.auto_corrector.AutoCorrector.parse_and_correct_log_file', return_value=True) as mock_correct:
            result = self.pipeline.parse_and_correct_log_file("log_file.log")
            self.assertTrue(result)
            mock_parse.assert_called_once_with("log_file.log")
            mock_correct.assert_called_once_with("log_file.log")

    def test_parse_and_correct_log_file_analysis_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=False) as mock_parse, \
             patch('skills.auto_corrector.AutoCorrector.parse_and_correct_log_file', return_value=True) as mock_correct:
            result = self.pipeline.parse_and_correct_log_file("log_file.log")
            self.assertFalse(result)
            mock_parse.assert_called_once_with("log_file.log")
            mock_correct.assert_not_called()

    def test_analyze_and_correct_signature_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.correct_code', return_value=True) as mock_correct:
            result = self.pipeline.analyze_and_correct_signature("sig")
            self.assertTrue(result)
            mock_analyze.assert_called_once_with("sig")
            mock_correct.assert_called_once_with("sig")

    def test_analyze_and_correct_signature_analysis_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=False) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.correct_code', return_value=True) as mock_correct:
            result = self.pipeline.analyze_and_correct_signature("sig")
            self.assertFalse(result)
            mock_analyze.assert_called_once_with("sig")
            mock_correct.assert_not_called()

    def test_process_error_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.apply_correction', return_value=True) as mock_correct:
            result = self.pipeline.process_error("sig")
            self.assertTrue(result)
            mock_analyze.assert_called_once_with("sig")
            mock_correct.assert_called_once_with("sig")

    def test_process_error_partial_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze, \
             patch('skills.auto_corrector.AutoCorrector.apply_correction', return_value=False) as mock_correct:
            result = self.pipeline.process_error("sig")
            self.assertFalse(result)
            mock_analyze.assert_called_once_with("sig")
            mock_correct.assert_called_once_with("sig")

    def test_pipeline_exception_handling(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', side_effect=Exception("Crash")):
            result = self.pipeline.process_error_stream("stream_data")
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()