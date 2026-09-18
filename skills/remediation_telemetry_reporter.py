from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class RemediationTelemetryReporter:
    """
    Модуль интеграции метрик процесса устранения уязвимостей с телеметрией состояния системы.
    """

    def __init__(self, metrics_collector=None, health_collector=None):
        self._metrics_collector = metrics_collector
        self._health_collector = health_collector

    @property
    def metrics_collector(self):
        if self._metrics_collector is not None:
            return self._metrics_collector
        return VulnerabilityRemediationMetricsCollector()

    @metrics_collector.setter
    def metrics_collector(self, value):
        self._metrics_collector = value

    @property
    def health_collector(self):
        if self._health_collector is not None:
            return self._health_collector
        return SystemHealthTelemetryCollector()

    @health_collector.setter
    def health_collector(self, value):
        self._health_collector = value

    def generate_remediation_telemetry_report(self, pipeline_id, module_name, incident_data,
                                              audit_summary, metrics, dashboard_format,
                                              incidents_list, patches_list, report_path):

        # Сбор метрик через VulnerabilityRemediationMetricsCollector
        for key, value in metrics.items():
            self.metrics_collector.collect_metric(pipeline_id, key, value)

        aggregated_metrics = self.metrics_collector.aggregate_pipeline_metrics(pipeline_id, metrics)

        # Агрегация телеметрии через SystemHealthTelemetryCollector
        telemetry_result = self.health_collector.collect_and_aggregate_telemetry(
            module_name, incident_data, audit_summary, metrics,
            dashboard_format, incidents_list, patches_list
        )

        # Экспорт отчета
        report_result = self.health_collector.export_comprehensive_report(telemetry_result, report_path)

        return {
            "report": report_result,
            "telemetry": telemetry_result
        }

    def process_stream_data(self, stream, report_path):
        return self.health_collector.process_telemetry_stream(stream, report_path)

    def report_telemetry_error(self, pipeline_id, error_context):
        return self.metrics_collector.handle_telemetry_error_sync(pipeline_id, error_context)

    def export_metrics(self, stream_identifier):
        return self.metrics_collector.export_metrics_stream(stream_identifier)

    def generate_unified_report(self, pipeline_id, incident_data, metrics, output_path):
        """
        Метод для интеграционного теста: связывает метрики с состоянием системы и сохраняет отчет.
        """
        # Агрегация данных
        health_data = self.health_collector.collect_and_aggregate_telemetry(
            module_name="remediation_reporter",
            incident_data=incident_data,
            audit_summary="success",
            metrics=metrics,
            dashboard_format="json",
            incidents_list=[incident_data.get("id")],
            patches_list=[pipeline_id]
        )

        # Формирование структуры отчета
        import json
        report_content = {
            "pipeline_id": pipeline_id,
            "incident_id": incident_data.get("id"),
            "health_status": health_data,
            "metrics": metrics
        }

        with open(output_path, 'w') as f:
            json.dump(report_content, f)

        return report_content