import unittest
from unittest.mock import patch, mock_open
import io
from skills.auto_corrector import (
    ErrorAnalyzer,
    AutoCorrector,
    has_critical_errors,
    analyze_errors,
    save_error_report
)

class TestAutoCorrector(unittest.TestCase):
    def setUp(self):
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()

    def test_parse_log_success(self):
        with patch("builtins.open", mock_open(read_data=b"log data")):
            result = self.analyzer.parse_log("dummy_path.log")
            self.assertTrue(result)

    def test_parse_log_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = self.analyzer.parse_log("nonexistent.log")
            self.assertFalse(result)

    def test_analyze_and_prevent_valid(self):
        result = self.analyzer.analyze_and_prevent("SOME_SIGNATURE")
        self.assertTrue(result)

    def test_analyze_and_prevent_empty(self):
        result = self.analyzer.analyze_and_prevent("")
        self.assertFalse(result)

    def test_process_stream_valid(self):
        stream = io.BytesIO(b"stream content")
        result = self.analyzer.process_stream(stream)
        self.assertTrue(result)

    def test_process_stream_none(self):
        with self.assertRaises(AttributeError):
            self.analyzer.process_stream(None)

    def test_auto_corrector_apply_fix_valid(self):
        result = self.corrector.apply_fix("SOME_SIGNATURE")
        self.assertTrue(result)

    def test_auto_corrector_apply_fix_empty(self):
        result = self.corrector.apply_fix("")
        self.assertFalse(result)

    def test_has_critical_errors_true(self):
        result = has_critical_errors("System failure CRITICAL occurred")
        self.assertTrue(result)

    def test_has_critical_errors_false(self):
        result = has_critical_errors("All systems normal")
        self.assertFalse(result)

    def test_analyze_errors(self):
        result = analyze_errors("Test Log")
        self.assertEqual(result, "Analysis report for: Test Log")

    def test_save_error_report_success(self):
        with patch("builtins.open", mock_open()) as mocked_file:
            result = save_error_report("some report", "report.log")
            self.assertTrue(result)
            mocked_file.assert_called_once_with("report.log", "w")

    def test_save_error_report_io_error(self):
        with patch("builtins.open", side_effect=IOError):
            result = save_error_report("some report", "report.log")
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()