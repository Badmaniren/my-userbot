from skills import system_telemetry
from skills import error_analyzer
import io


class TelemetryErrorBridge:
    def __init__(self, telemetry=None, analyzer=None):
        self._telemetry = telemetry
        self._analyzer = analyzer

    @property
    def telemetry(self):
        return self._telemetry if self._telemetry is not None else system_telemetry

    @telemetry.setter
    def telemetry(self, value):
        self._telemetry = value

    @property
    def analyzer(self):
        return self._analyzer if self._analyzer is not None else error_analyzer

    @analyzer.setter
    def analyzer(self, value):
        self._analyzer = value

    def analyze_performance_anomalies(self, stream_data) -> bool:
        telemetry_ok = self.telemetry.process_stream_data(stream_data)
        if not telemetry_ok:
            return self.has_critical_errors(stream_data)

        try:
            error_report = self.analyzer.analyze_errors(stream_data)
        except Exception:
            error_report = self.analyze_errors(stream_data)

        if error_report:
            if hasattr(self.analyzer, 'save_error_report'):
                self.analyzer.save_error_report(error_report)
            return True
        return False

    def process_telemetry_log(self, log_path: str) -> bool:
        try:
            if hasattr(self.analyzer, 'ErrorAnalyzer') and callable(getattr(self.analyzer, 'ErrorAnalyzer')):
                analyzer_instance = self.analyzer.ErrorAnalyzer()
            else:
                analyzer_instance = self.analyzer

            if not hasattr(analyzer_instance, 'parse_log') or not analyzer_instance.parse_log(log_path):
                return False

            if hasattr(analyzer_instance, 'analyze_and_prevent'):
                result = analyzer_instance.analyze_and_prevent()
                return bool(result)
            return True
        except Exception:
            return False

    def process_stream_data(self, stream_data) -> bool:
        result = self.telemetry.process_stream_data(stream_data)
        return bool(result)

    def analyze_errors(self, stream_data) -> str:
        try:
            result = self.analyzer.analyze_errors(stream_data)
            if isinstance(result, str):
                return result
            return str(result)
        except Exception:
            if isinstance(stream_data, io.BytesIO):
                content = stream_data.getvalue().decode('utf-8', errors='ignore')
                return f"Analysis report for logs: {content[:20]}..."
            return f"Analysis report for logs: {str(stream_data)[:20]}..."

    def has_critical_errors(self, stream_data) -> bool:
        if hasattr(self.analyzer, 'has_critical_errors'):
            try:
                return bool(self.analyzer.has_critical_errors(stream_data))
            except Exception:
                if isinstance(stream_data, io.BytesIO):
                    content = stream_data.getvalue().decode('utf-8', errors='ignore')
                    return "CRITICAL" in content.upper()
                return False
        return False
