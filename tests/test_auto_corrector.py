import unittest
from unittest.mock import patch, MagicMock
import io
import requests
from skills.auto_corrector import AutoCorrector


class TestAutoCorrector(unittest.TestCase):

    def setUp(self):
        self.corrector = AutoCorrector()

    def test_correct_code_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze:
            res = self.corrector.correct_code("TypeError: unsupported operand")
            mock_analyze.assert_called_once_with("TypeError: unsupported operand")
            self.assertTrue(res)

    def test_correct_code_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=False) as mock_analyze:
            res = self.corrector.correct_code("UnknownError")
            self.assertFalse(res)

    def test_correct_code_exception(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', side_effect=Exception("Critical fail")):
            res = self.corrector.correct_code("FaultyError")
            self.assertFalse(res)

    def test_process_error_stream_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', return_value=True) as mock_stream:
            stream_data = io.BytesIO(b'stream content')
            res = self.corrector.process_error_stream(stream_data)
            mock_stream.assert_called_once_with(stream_data)
            self.assertTrue(res)

    def test_process_error_stream_exception(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.process_stream', side_effect=Exception("Stream error")):
            stream_data = io.BytesIO(b'bad stream')
            res = self.corrector.process_error_stream(stream_data)
            self.assertFalse(res)

    def test_parse_and_correct_log_file_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', return_value=True) as mock_parse:
            res = self.corrector.parse_and_correct_log_file('/path/to/logs.log')
            mock_parse.assert_called_once_with('/path/to/logs.log')
            self.assertTrue(res)

    def test_parse_and_correct_log_file_not_found(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', side_effect=FileNotFoundError):
            res = self.corrector.parse_and_correct_log_file('/nonexistent/path.log')
            self.assertFalse(res)

    def test_parse_and_correct_log_file_exception(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.parse_log', side_effect=Exception("Parse error")):
            res = self.corrector.parse_and_correct_log_file('/path/to/error.log')
            self.assertFalse(res)

    def test_verify_fix_via_web_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '<html><body>Fixed</body></html>'
            mock_get.return_value = mock_response

            res = self.corrector.verify_fix_via_web('http://example.com/fix')
            mock_get.assert_called_once_with('http://example.com/fix')
            self.assertTrue(res)

    def test_verify_fix_via_web_bad_status(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            res = self.corrector.verify_fix_via_web('http://example.com/notfound')
            self.assertFalse(res)

    def test_verify_fix_via_web_exception(self):
        with patch('requests.get', side_effect=requests.RequestException("Network down")):
            res = self.corrector.verify_fix_via_web('http://example.com/error')
            self.assertFalse(res)

    def test_apply_correction_success(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=True) as mock_analyze:
            res = self.corrector.apply_correction("IndexError: list index out of range")
            mock_analyze.assert_called_once_with("IndexError: list index out of range")
            self.assertTrue(res)

    def test_apply_correction_failure(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', return_value=False):
            res = self.corrector.apply_correction("UnfixableError")
            self.assertFalse(res)

    def test_apply_correction_exception(self):
        with patch('skills.error_analyzer.ErrorAnalyzer.analyze_and_prevent', side_effect=Exception("Fail")):
            res = self.corrector.apply_correction("BrokenError")
            self.assertFalse(res)