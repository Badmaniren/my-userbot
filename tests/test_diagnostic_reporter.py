import unittest
from unittest.mock import patch, MagicMock
import io

from skills.diagnostic_reporter import DiagnosticReporter
from skills.ai_diagnostic_agent import ErrorAnalyzer, AutoCorrector
from skills.error_pipeline import ErrorPipeline


class TestDiagnosticReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = DiagnosticReporter()

    def test_init_composition_dependencies(self):
        self.assertIsInstance(self.reporter.error_analyzer, ErrorAnalyzer)
        self.assertIsInstance(self.reporter.auto_corrector, AutoCorrector)
        self.assertIsInstance(self.reporter.error_pipeline, ErrorPipeline)

    def test_generate_report_success(self):
        log_path = "test_system.log"
        stream_data = io.BytesIO(b"CRITICAL ERROR 500")

        with patch.object(ErrorAnalyzer, 'parse_log', return_value=True) as mock_parse, \
             patch.object(ErrorPipeline, 'run_pipeline', return_value=True) as mock_pipeline, \
             patch('skills.ai_diagnostic_agent.save_error_report', return_value=True) as mock_save:

            result = self.reporter.generate_report(log_path, stream_data)
            self.assertTrue(result)
            mock_parse.assert_called_once_with(log_path)
            mock_pipeline.assert_called_once_with(log_path)
            mock_save.assert_called_once()

    def test_generate_report_analyzer_failure(self):
        log_path = "bad_system.log"
        stream_data = io.BytesIO(b"INFO OK")

        with patch.object(ErrorAnalyzer, 'parse_log', return_value=False) as mock_parse, \
             patch.object(ErrorPipeline, 'run_pipeline', return_value=True) as mock_pipeline:

            result = self.reporter.generate_report(log_path, stream_data)
            self.assertFalse(result)
            mock_parse.assert_called_once_with(log_path)

    def test_generate_report_pipeline_failure(self):
        log_path = "pipeline_fail.log"
        stream_data = io.BytesIO(b"WARN")

        with patch.object(ErrorAnalyzer, 'parse_log', return_value=True), \
             patch.object(ErrorPipeline, 'run_pipeline', return_value=False) as mock_pipeline:

            result = self.reporter.generate_report(log_path, stream_data)
            self.assertFalse(result)
            mock_pipeline.assert_called_once_with(log_path)

    def test_process_stream_aggregation(self):
        stream_data = io.BytesIO(b"STREAM_ERROR_SIGNATURE")

        with patch.object(ErrorPipeline, 'process_stream_pipeline', return_value=True) as mock_stream_pipe, \
             patch.object(AutoCorrector, 'process_error_stream', return_value=True) as mock_auto_stream:

            result = self.reporter.process_stream_aggregation(stream_data)
            self.assertTrue(result)
            mock_stream_pipe.assert_called_once()
            mock_auto_stream.assert_called_once()

    def test_process_stream_aggregation_exception_handling(self):
        stream_data = MagicMock()
        stream_data.read.side_effect = Exception("Stream read error")

        result = self.reporter.process_stream_aggregation(stream_data)
        self.assertFalse(result)

    def test_verify_system_health(self):
        url = "http://localhost/health"

        with patch.object(ErrorPipeline, 'verify_pipeline_fix', return_value=True) as mock_verify:
            result = self.reporter.verify_system_health(url)
            self.assertTrue(result)
            mock_verify.assert_called_once_with(url)

    def test_verify_system_health_failure(self):
        url = "http://localhost/health"

        with patch.object(ErrorPipeline, 'verify_pipeline_fix', return_value=False) as mock_verify:
            result = self.reporter.verify_system_health(url)
            self.assertFalse(result)
            mock_verify.assert_called_once_with(url)

    def test_verify_system_health_raises(self):
        url = "invalid_url"

        with patch.object(ErrorPipeline, 'verify_pipeline_fix', side_effect=ValueError("Invalid URL")):
            with self.assertRaises(ValueError):
                self.reporter.verify_system_health(url)


if __name__ == '__main__':
    unittest.main()