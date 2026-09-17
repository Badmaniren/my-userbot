import io
import os
from typing import Any, Dict, List, BinaryIO

from skills.telemetry_processor import TelemetryProcessor
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TelemetryHealthPipelineException(Exception):
    """Исключение для ошибок в конвейере телеметрии и здоровья системы."""
    pass


class TelemetryHealthPipeline:
    def __init__(self) -> None:
        self.processor = TelemetryProcessor()
        self.collector = SystemHealthTelemetryCollector()
        # Для интеграционных тестов с прямым обращением к атрибуту
        self.telemetry_processor = self.processor

    def execute_stream_pipeline(self, stream: Any, output_path: str) -> Dict[str, Any]:
        if not isinstance(stream, (io.IOBase, BinaryIO)):
            raise TelemetryHealthPipelineException("Invalid stream type, expected binary stream.")
        try:
            result = self.collector.process_telemetry_stream(stream, output_path)
            if not isinstance(result, dict):
                # Если коллектор вернул не словарь (например, True/строку), упаковываем его в структуру словаря
                return {"status": "success", "result": result}
            return result
        except Exception as e:
            if isinstance(e, TelemetryHealthPipelineException):
                raise
            raise TelemetryHealthPipelineException(f"Pipeline execution failed: {e}") from e

    def run_full_pipeline(
        self,
        module_name: str,
        incident_data: Dict[str, Any],
        audit_summary: Dict[str, Any],
        metrics: Dict[str, float],
        dashboard_format: str,
        incidents_list: List[Any],
        patches_list: List[Any],
        report_path: str,
        dashboard_path: str
    ) -> Dict[str, Any]:
        try:
            return self.collector.collect_and_process_telemetry(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list,
                report_path,
                dashboard_path
            )
        except Exception as e:
            if isinstance(e, TelemetryHealthPipelineException):
                raise
            raise TelemetryHealthPipelineException(f"Full pipeline run failed: {e}") from e

    def export_report(self, payload: Dict[str, Any], export_path: str) -> None:
        try:
            self.collector.export_comprehensive_report(payload, export_path)
        except Exception as e:
            if isinstance(e, TelemetryHealthPipelineException):
                raise
            raise TelemetryHealthPipelineException(f"Export report failed: {e}") from e


def run_telemetry_health_pipeline(*args: Any, **kwargs: Any) -> Any:
    """Запускает конвейер телеметрии с автоматическим выбором потока или полного режима."""
    pipeline = TelemetryHealthPipeline()
    if args and isinstance(args[0], (io.IOBase, BinaryIO)):
        return pipeline.execute_stream_pipeline(*args, **kwargs)
    return pipeline.run_full_pipeline(*args, **kwargs)


telemetry_health_pipeline = TelemetryHealthPipeline