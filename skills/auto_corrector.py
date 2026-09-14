import requests
from bs4 import BeautifulSoup
from skills.error_analyzer import ErrorAnalyzer


class AutoCorrector:
    def __init__(self):
        self.analyzer = ErrorAnalyzer()

    def correct_code(self, error_signature: str) -> bool:
        try:
            res = self.analyzer.analyze_and_prevent(error_signature)
            if res is None:
                return True
            return bool(res)
        except Exception:
            return False

    def process_error_stream(self, stream_data) -> bool:
        try:
            res = self.analyzer.process_stream(stream_data)
            if res is None:
                return True
            return bool(res)
        except Exception:
            return False

    def parse_and_correct_log_file(self, log_path: str) -> bool:
        try:
            res = self.analyzer.parse_log(log_path)
            if res is None:
                return True
            return bool(res)
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def verify_fix_via_web(self, url: str) -> bool:
        try:
            response = requests.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def apply_correction(self, error_signature: str) -> bool:
        try:
            res = self.analyzer.analyze_and_prevent(error_signature)
            if res is None:
                return True
            return bool(res)
        except Exception:
            return False