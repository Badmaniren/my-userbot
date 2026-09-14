from skills import system_telemetry, error_pipeline
from skills.system_telemetry import SystemTelemetry
from skills.error_pipeline import ErrorPipeline

class TelemetryOptimizer:
    def __init__(self):
        try:
            self.telemetry = SystemTelemetry()
        except Exception:
            self.telemetry = None
        try:
            self.pipeline = ErrorPipeline()
        except Exception:
            self.pipeline = None

    def optimize_pipeline(self, metrics_source: str) -> bool:
        try:
            telemetry = SystemTelemetry()
            if not hasattr(telemetry, 'collect'):
                return False
            telemetry_data = telemetry.collect(metrics_source)
        except Exception:
            return False

        try:
            pipeline = ErrorPipeline()
            result = pipeline.run_pipeline(telemetry_data)
            return bool(result)
        except Exception:
            return False

    def process_stream_optimization(self, stream_data) -> bool:
        if hasattr(stream_data, 'read'):
            data = stream_data.read()
        else:
            data = stream_data
        try:
            pipeline = ErrorPipeline()
            result = pipeline.process_stream_pipeline(data)
            return bool(result)
        except Exception:
            return False
