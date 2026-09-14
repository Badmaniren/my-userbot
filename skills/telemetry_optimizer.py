import requests
from skills import system_telemetry
from skills import error_pipeline


class TelemetryOptimizer:
    def __init__(self):
        self.telemetry = system_telemetry.SystemTelemetry()
        self.pipeline = error_pipeline.ErrorPipeline()

    def optimize_pipeline(self, log_path: str) -> bool:
        return self.pipeline.run_pipeline(log_path)

    def process_telemetry_stream(self, stream) -> bool:
        try:
            return system_telemetry.process_stream_data(stream)
        except Exception:
            return False

    def verify_optimization(self, url: str) -> bool:
        try:
            response = requests.get(url)
            return response.status_code == 200
        except Exception:
            return False