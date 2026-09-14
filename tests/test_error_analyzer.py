import unittest
from unittest.mock import patch, mock_open
import io
from skills.error_analyzer import ErrorAnalyzer


class TestErrorAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = ErrorAnalyzer()

    def test_analyze_file_success(self):
        log_content = "ERROR: Test failed due to timeout\nCRITICAL: Recursion detected"
        mock_file = mock_open(read_data=log_content)

        with patch("builtins.open", mock_file):
            result = self.analyzer.analyze_file("dummy_path.log")
            self.assertTrue(result)

    def test_analyze_file_empty(self):
        mock_file = mock_open(read_data="")

        with patch("builtins.open", mock_file):
            result = self.analyzer.analyze_file("empty.log")
            self.assertFalse(result)

    def test_analyze_stream_bytes(self):
        stream_data = io.BytesIO(b"FATAL: Segfault in module X")

        with patch("skills.error_analyzer.requests.get") as mock_get:
            mock_get.return_value.raw = stream_data
            mock_get.return_value.status_code = 200

            result = self.analyzer.analyze_stream("http://example.com/log")
            self.assertTrue(result)

    def test_analyze_file_not_found_raises(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                self.analyzer.analyze_file("nonexistent.log")

    def test_analyze_file_permission_error_safe(self):
        with patch("builtins.open", side_effect=PermissionError):
            result = self.analyzer.analyze_file("restricted.log")
            self.assertFalse(result)

    def test_parse_error_signature_valid(self):
        error_line = "Traceback (most recent call last): RuntimeError: Recursive loop"
        result = self.analyzer.parse_signature(error_line)
        self.assertTrue(result)

    def test_parse_error_signature_invalid(self):
        normal_line = "INFO: All systems operational"
        result = self.analyzer.parse_signature(normal_line)
        self.assertFalse(result)

    def test_check_recursion_prevention_detected(self):
        history = ["Error: timeout", "Error: timeout", "Error: timeout"]
        result = self.analyzer.detect_recursion(history)
        self.assertTrue(result)

    def test_check_recursion_prevention_clean(self):
        history = ["Error: timeout", "Warning: high memory", "Info: reboot"]
        result = self.analyzer.detect_recursion(history)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()