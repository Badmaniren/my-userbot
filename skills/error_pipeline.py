from skills import error_analyzer
from skills import auto_corrector
from skills.error_analyzer import ErrorAnalyzer
from skills.auto_corrector import AutoCorrector


class ErrorPipeline:
    def __init__(self):
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()

    def process_error_stream(self, stream_data):
        try:
            analysis = self.analyzer.process_stream(stream_data)
            if not analysis:
                return False
            correction = self.corrector.process_error_stream(stream_data)
            return bool(correction)
        except Exception:
            return False

    def parse_and_correct_log_file(self, log_file):
        try:
            analysis = self.analyzer.parse_log(log_file)
            if not analysis:
                return False
            correction = self.corrector.parse_and_correct_log_file(log_file)
            return bool(correction)
        except Exception:
            return False

    def analyze_and_correct_signature(self, signature):
        try:
            analysis = self.analyzer.analyze_and_prevent(signature)
            if not analysis:
                return False
            correction = self.corrector.correct_code(signature)
            return bool(correction)
        except Exception:
            return False

    def process_error(self, signature):
        try:
            analysis = self.analyzer.analyze_and_prevent(signature)
            if not analysis:
                return False
            correction = self.corrector.apply_correction(signature)
            return bool(correction)
        except Exception:
            return False
