import io
from skills import system_telemetry
from skills.error_pipeline import ErrorPipeline


class TelemetryErrorBridge:
    def __init__(self):
        self.telemetry = system_telemetry
        self.pipeline = ErrorPipeline()

    def process_telemetry_and_errors(self, stream: io.BytesIO) -> bool:
        try:
            data = stream.read()
            telemetry_res = system_telemetry.process_stream_data(data)
            pipeline_res = self.pipeline.process_stream_pipeline(data)
            return bool(telemetry_res and pipeline_res)
        except Exception:
            return False