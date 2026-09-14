from skills.error_analyzer import ErrorAnalyzer
from skills.auto_corrector import AutoCorrector

class ErrorPipeline:
    def __init__(self):
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()

    def run_pipeline(self, log_path: str) -> bool:
        try:
            parsed = self.analyzer.parse_log(log_path)
        except Exception:
            raise
        
        if not parsed:
            return False
        
        analyzed = self.analyzer.analyze_and_prevent(log_path)
        if not analyzed:
            return False

        corrected = self.corrector.correct_code(log_path)
        return bool(corrected)

    def process_stream_pipeline(self, stream) -> bool:
        analyzed = self.analyzer.process_stream(stream)
        corrected = self.corrector.process_error_stream(stream)
        return bool(analyzed and corrected)

    def verify_pipeline_fix(self, url: str) -> bool:
        verified = self.corrector.verify_fix_via_web(url)
        return bool(verified)

    def process_error_stream(self, error_signature: str) -> bool:
        analyzed = self.analyzer.analyze_and_prevent(error_signature)
        corrected = self.corrector.correct_code(error_signature)
        return bool(analyzed and corrected)