import io
from skills.system_telemetry import SystemTelemetry, process_stream_data
from skills.error_analyzer import ErrorAnalyzer, analyze_errors, has_critical_errors, save_error_report


class TelemetryAnalyzer:
    def __init__(self):
        self.telemetry = SystemTelemetry()
        self.error_analyzer = ErrorAnalyzer()

    def analyze_system_health(self, log_path: str) -> bool:
        try:
            parsed = self.error_analyzer.parse_log(log_path)
            if not parsed:
                return False
            result = self.error_analyzer.analyze_and_prevent(log_path)
            return bool(result)
        except Exception:
            return False

    def process_telemetry_stream(self, stream) -> bool:
        try:
            if hasattr(stream, "read"):
                data = stream.read()
            else:
                data = stream

            processed_telemetry = process_stream_data(data)

            stream_for_errors = io.BytesIO(data) if isinstance(data, bytes) else stream
            processed_errors = self.error_analyzer.process_stream(stream_for_errors)
            return bool(processed_telemetry and processed_errors)
        except Exception:
            return False

    def generate_complex_metrics(self, log_path: str) -> bool:
        try:
            report = analyze_errors(log_path)
            if report:
                return True
            return False
        except Exception:
            return False