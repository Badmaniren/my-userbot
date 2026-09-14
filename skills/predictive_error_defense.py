from skills.predictive_error_detector import PredictiveFaultDetector
from skills.error_pipeline import ErrorPipeline

class PredictiveErrorDefense:
    def __init__(self):
        self.detector = PredictiveFaultDetector()
        self.pipeline = ErrorPipeline()

    def detect_and_prevent(self, log_path: str) -> bool:
        anomalies = self.detector.detect(log_path) if hasattr(self.detector, 'detect') else True
        if anomalies:
            return self.pipeline.run_pipeline(log_path)
        return False

    def process_stream_defense(self, stream_data) -> bool:
        try:
            return self.pipeline.process_stream_pipeline(stream_data)
        except Exception:
            raise

    def verify_defense_fix(self, url: str) -> bool:
        return self.pipeline.verify_pipeline_fix(url)

    def handle_signature_defense(self, signature: str) -> bool:
        return self.pipeline.process_error_stream(signature)