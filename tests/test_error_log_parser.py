import unittest
from unittest.mock import patch, MagicMock
import io
from skills.error_log_parser import ErrorLogParser


class TestErrorLogParser(unittest.TestCase):

    def setUp(self):
        self.parser = ErrorLogParser()

    def test_parse_error_log_success(self):
        sample_log = b"[ERROR] 2023-10-27: Connection timeout in module auth"
        mock_stream = io.BytesIO(sample_log)

        with patch('skills.error_log_parser.open', return_value=mock_stream):
            result = self.parser.parse_log("dummy_path.log")
            self.assertTrue(bool(result))

    def test_parse_error_log_empty(self):
        mock_stream = io.BytesIO(b"")

        with patch('skills.error_log_parser.open', return_value=mock_stream):
            result = self.parser.parse_log("empty.log")
            self.assertFalse(bool(result))

    def test_categorize_error_known(self):
        error_message = "NullPointerException at line 42"
        category = self.parser.categorize(error_message)
        self.assertTrue(bool(category))

    def test_categorize_error_unknown(self):
        error_message = "A totally bizarre and unprecedented anomaly"
        category = self.parser.categorize(error_message)
        self.assertFalse(bool(category))

    def test_parse_log_raises_exception_on_corruption(self):
        with patch('skills.error_log_parser.open', side_effect=IOError("Disk failure")):
            with self.assertRaises(IOError):
                self.parser.parse_log("corrupted.log")

    def test_safe_parse_handles_exception_gracefully(self):
        with patch('skills.error_log_parser.open', side_effect=IOError("Disk failure")):
            result = self.parser.safe_parse("corrupted.log")
            self.assertFalse(bool(result))