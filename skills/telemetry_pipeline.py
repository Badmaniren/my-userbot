from skills.system_telemetry import SystemTelemetry
from skills.error_pipeline import ErrorPipeline


class TelemetryPipelineOptimizer:
    def __init__(self):
        self.telemetry = SystemTelemetry()
        self.error_pipeline = ErrorPipeline()

    def run_telemetry_pipeline(self, log_path: str) -> bool:
        try:
            return bool(self.error_pipeline.run_pipeline(log_path))
        except Exception:
            return False

    def process_telemetry_stream(self, stream_data) -> bool:
        if hasattr(self.telemetry, "process_stream_data"):
            try:
                self.telemetry.process_stream_data(stream_data)
            except AttributeError:
                pass
        return bool(self.error_pipeline.process_stream_pipeline(stream_data))

    def verify_and_optimize(self, url: str) -> bool:
        return bool(self.error_pipeline.verify_pipeline_fix(url))

    def process_stream_data(self, stream_data) -> bool:
        if hasattr(self, "telemetry") and hasattr(self.telemetry, "process_stream_data"):
            self.telemetry.process_stream_data(stream_data)
        return self.process_telemetry_stream(stream_data)


TelemetryPipeline = TelemetryPipelineOptimizer