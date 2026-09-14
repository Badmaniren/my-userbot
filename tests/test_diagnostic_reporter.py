import unittest
from unittest.mock import patch, MagicMock
import io
from skills.diagnostic_reporter import DiagnosticReporter

class TestDiagnosticReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = DiagnosticReporter()

    @patch('skills.diagnostic_reporter.save_error_report')
    def test_generate_report_success(self, mock_save):
        with patch.object(self.reporter.error_analyzer, 'parse_log', return_value=True), \
             patch.object(self.reporter.error_pipeline, 'run_pipeline', return_value=True):
            mock_save.return_value = True
            
            result = self.reporter.generate_report('test_system.log')
            self.assertTrue(result)
            mock_save.assert_called_once()

    def test_generate_report_parse_fails(self):
        with patch.object(self.reporter.error_analyzer, 'parse_log', return_value=False):
            result = self.reporter.generate_report('test_system.log')
            self.assertFalse(result)

    def test_generate_report_pipeline_fails(self):
        with patch.object(self.reporter.error_analyzer, 'parse_log', return_value=True), \
             patch.object(self.reporter.error_pipeline, 'run_pipeline', return_value=False):
            result = self.reporter.generate_report('test_system.log')
            self.assertFalse(result)

    @patch('skills.diagnostic_reporter.save_error_report')
    def test_generate_report_save_fails(self, mock_save):
        with patch.object(self.reporter.error_analyzer, 'parse_log', return_value=True), \
             patch.object(self.reporter.error_pipeline, 'run_pipeline', return_value=True):
            mock_save.return_value = False
            
            result = self.reporter.generate_report('test_system.log')
            self.assertFalse(result)

    def test_generate_report_exception_raises(self):
        with patch.object(self.reporter.error_analyzer, 'parse_log', side_effect=Exception("Critical error")):
            with self.assertRaises(Exception):
                self.reporter.generate_report('test_system.log')

    def test_process_stream_aggregation_success(self):
        stream_mock = io.BytesIO(b'stream data')
        with patch.object(self.reporter.error_pipeline, 'process_stream_pipeline', return_value=True), \
             patch.object(self.reporter.auto_corrector, 'process_error_stream', return_value=True):
            
            result = self.reporter.process_stream_aggregation(stream_mock)
            self.assertTrue(result)

    def test_process_stream_aggregation_pipeline_false(self):
        stream_mock = io.BytesIO(b'stream data')
        with patch.object(self.reporter.error_pipeline, 'process_stream_pipeline', return_value=False), \
             patch.object(self.reporter.auto_corrector, 'process_error_stream', return_value=True):
            
            result = self.reporter.process_stream_aggregation(stream_mock)
            self.assertFalse(result)

    def test_process_stream_aggregation_corrector_false(self):
        stream_mock = io.BytesIO(b'stream data')
        with patch.object(self.reporter.error_pipeline, 'process_stream_pipeline', return_value=True), \
             patch.object(self.reporter.auto_corrector, 'process_error_stream', return_value=False):
            
            result = self.reporter.process_stream_aggregation(stream_mock)
            self.assertFalse(result)

    def test_process_stream_aggregation_exception_catches(self):
        stream_mock = io.BytesIO(b'stream data')
        with patch.object(self.reporter.error_pipeline, 'process_stream_pipeline', side_effect=Exception("Stream fail")):
            result = self.reporter.process_stream_aggregation(stream_mock)
            self.assertFalse(result)

    def test_verify_system_health_success(self):
        with patch.object(self.reporter.error_pipeline, 'verify_pipeline_fix', return_value=True):
            result = self.reporter.verify_system_health('http://localhost/health')
            self.assertTrue(result)

    def test_verify_system_health_failure(self):
        with patch.object(self.reporter.error_pipeline, 'verify_pipeline_fix', return_value=False):
            result = self.reporter.verify_system_health('http://localhost/health')
            self.assertFalse(result)

    def test_verify_system_health_exception_raises(self):
        with patch.object(self.reporter.error_pipeline, 'verify_pipeline_fix', side_effect=Exception("Network error")):
            with self.assertRaises(Exception):
                self.reporter.verify_system_health('http://localhost/health')

if __name__ == '__main__':
    unittest.main()