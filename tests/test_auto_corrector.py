import unittest
from unittest.mock import patch, MagicMock
import io
import requests
from bs4 import BeautifulSoup

from skills.auto_corrector import AutoCorrector


class TestAutoCorrector(unittest.TestCase):
    def setUp(self):
        self.corrector = AutoCorrector()

    def test_correct_code_success(self):
        error_signature = "NameError: name 'undefined_var' is not defined"
        with patch('skills.auto_corrector.ErrorAnalyzer') as mock_analyzer_cls:
            mock_instance = mock_analyzer_cls.return_value
            mock_instance.analyze_and_prevent.return_value = True
            
            res = self.corrector.correct_code(error_signature)
            self.assertTrue(res)

    def test_correct_code_failure(self):
        error_signature = "SyntaxError: invalid syntax"
        with patch('skills.auto_corrector.ErrorAnalyzer') as mock_analyzer_cls:
            mock_instance = mock_analyzer_cls.return_value
            mock_instance.analyze_and_prevent.return_value = False
            
            res = self.corrector.correct_code(error_signature)
            self.assertFalse(res)

    def test_correct_code_exception_handling(self):
        error_signature = "TypeError: unsupported operand type"
        with patch('skills.auto_corrector.ErrorAnalyzer') as mock_analyzer_cls:
            mock_instance = mock_analyzer_cls.return_value
            mock_instance.analyze_and_prevent.side_effect = Exception("Analyzer failure")
            
            res = self.corrector.correct_code(error_signature)
            self.assertFalse(res)

    def test_process_error_stream(self):
        stream_data = io.BytesIO(b"CRITICAL ERROR: NullPointerException")
        with patch('skills.auto_corrector.ErrorAnalyzer') as mock_analyzer_cls:
            mock_instance = mock_analyzer_cls.return_value
            mock_instance.process_stream.return_value = True
            
            res = self.corrector.process_error_stream(stream_data)
            self.assertTrue(res)

    def test_parse_and_correct_log_file(self):
        log_path = "/var/log/error.log"
        with patch('skills.auto_corrector.ErrorAnalyzer') as mock_analyzer_cls:
            mock_instance = mock_analyzer_cls.return_value
            mock_instance.parse_log.return_value = True
            
            res = self.corrector.parse_and_correct_log_file(log_path)
            self.assertTrue(res)

    def test_verify_fix_via_web(self):
        url = "http://localhost:8000/health"
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>OK</body></html>"
            mock_get.return_value = mock_response

            res = self.corrector.verify_fix_via_web(url)
            self.assertTrue(res)