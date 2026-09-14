import unittest
from unittest.mock import patch
import io
from skills.error_analyzer import ErrorAnalyzer


class TestErrorAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ErrorAnalyzer()

    def test_parse_error_log_success(self):
        log_content = b"ERROR: Division by zero at module main.py line 42"
        mock_file = io.BytesIO(log_content)

        with patch("skills.error_analyzer.open", return_value=mock_file):
            result = self.analyzer.parse_log("dummy_path.log")
            self.assertTrue(bool(result))

    def test_parse_error_log_empty(self):
        log_content = b""
        mock_file = io.BytesIO(log_content)

        with patch("skills.error_analyzer.open", return_value=mock_file):
            result = self.analyzer.parse_log("empty_path.log")
            self.assertFalse(result)

    def test_retrospective_analysis_prevents_failure(self):
        error_signature = "NullPointerException in auth.py"
        with patch.object(self.analyzer, "_query_knowledge_base", return_value=True):
            result = self.analyzer.analyze_and_prevent(error_signature)
            self.assertTrue(result)

    def test_retrospective_analysis_unknown_error(self):
        error_signature = "Unknown quantum flux failure"
        with patch.object(self.analyzer, "_query_knowledge_base", return_value=False):
            result = self.analyzer.analyze_and_prevent(error_signature)
            self.assertFalse(result)

    def test_analyzer_raises_exception_on_corrupted_data(self):
        with patch.object(self.analyzer, "_parse_raw_stream", side_effect=ValueError("Corrupted stream")):
            with self.assertRaises(ValueError):
                self.analyzer.process_stream(io.BytesIO(b"corrupted"))

    def test_analyzer_handles_safe_failure_without_crashing(self):
        with patch.object(self.analyzer, "_parse_raw_stream", side_effect=Exception("Unexpected crash")):
            result = self.analyzer.process_stream(io.BytesIO(b"bad data"))
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()