import unittest
from unittest.mock import patch, mock_open
import io

from skills.error_analyzer import (
    ErrorAnalyzer,
    has_critical_errors,
    analyze_errors,
    save_error_report
)


class TestErrorAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ErrorAnalyzer()

    def test_parse_log_success(self):
        m = mock_open(read_data=b"some log content")
        with patch("skills.error_analyzer.open", m):
            result = self.analyzer.parse_log("dummy_path.log")
            self.assertTrue(result)

    def test_parse_log_empty(self):
        m = mock_open(read_data=b"")
        with patch("skills.error_analyzer.open", m):
            result = self.analyzer.parse_log("dummy_path.log")
            self.assertFalse(result)

    def test_query_knowledge_base_true(self):
        result = self.analyzer._query_knowledge_base("Exception: NullPointerException occurred")
        self.assertTrue(result)

    def test_query_knowledge_base_false(self):
        result = self.analyzer._query_knowledge_base("IndexError: list index out of range")
        self.assertFalse(result)

    def test_analyze_and_prevent(self):
        with patch.object(self.analyzer, "_query_knowledge_base", return_value=True) as mock_qb:
            result = self.analyzer.analyze_and_prevent("NullPointerException")
            self.assertTrue(result)
            mock_qb.assert_called_once_with("NullPointerException")

    def test_process_stream_success(self):
        stream = io.BytesIO(b"normal stream data")
        result = self.analyzer.process_stream(stream)
        self.assertTrue(result)

    def test_process_stream_value_error(self):
        stream = io.BytesIO(b"corrupted stream data")
        with self.assertRaises(ValueError):
            self.analyzer.process_stream(stream)

    def test_process_stream_unexpected_crash(self):
        stream = io.BytesIO(b"bad data inside stream")
        result = self.analyzer.process_stream(stream)
        self.assertFalse(result)

    def test_has_critical_errors_true(self):
        logs = "INFO: init\nCRITICAL: system failure\n"
        self.assertTrue(has_critical_errors(logs))

    def test_has_critical_errors_false(self):
        logs = "INFO: init\nWARNING: low memory\n"
        self.assertFalse(has_critical_errors(logs))

    def test_analyze_errors(self):
        logs = "A" * 30
        report = analyze_errors(logs)
        self.assertIn("Analysis report for logs:", report)
        self.assertIn("A" * 20, report)

    def test_save_error_report_success(self):
        self.assertTrue(save_error_report("Valid report"))

    def test_save_error_report_empty(self):
        self.assertFalse(save_error_report(""))


if __name__ == "__main__":
    unittest.main()