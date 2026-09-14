import requests
from bs4 import BeautifulSoup
from skills.error_analyzer import ErrorAnalyzer


class AutoCorrector:
    def __init__(self):
        self.analyzer = ErrorAnalyzer()

    def correct_code(self, error_signature: str) -> bool:
        try:
            return bool(self.analyzer.analyze_and_prevent(error_signature))
        except Exception:
            return False

    def process_error_stream(self, stream_data) -> bool:
        return bool(self.analyzer.process_stream(stream_data))

    def parse_and_correct_log_file(self, log_path: str) -> bool:
        return bool(self.analyzer.parse_log(log_path))

    def verify_fix_via_web(self, url: str) -> bool:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return bool(soup)
        return False

    def apply_correction(self, error_signature: str) -> bool:
        return bool(self.analyzer.analyze_and_prevent(error_signature))