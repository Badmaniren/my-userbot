import json
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter

class AuditExportBridge:
    """
    Bridge module to facilitate the transfer of aggregated anomaly reports
    from the audit hub to the export system.
    """

    def __init__(self, repo_path_or_hub, log_path_or_exporter=None, threshold=None):
        # Поддержка двух способов инициализации: через пути (для юнит-тестов с моками)
        # или через готовые инстансы (для интеграционных тестов)
        if hasattr(repo_path_or_hub, "generate_final_report"):
            self.hub = repo_path_or_hub
            self.exporter = log_path_or_exporter
        else:
            self.hub = AnomalyAuditHub(repo_path_or_hub, log_path_or_exporter, threshold)
            self.exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)

    def transfer_report(self, output_path):
        """Извлекает отчет из Hub и передает в Exporter."""
        report = self.hub.generate_final_report()
        return self.exporter.export_json_report(output_path)

    def aggregate_and_push(self, metric_name, metric_value, output_path):
        """Агрегирует данные и инициирует экспорт."""
        self.hub.aggregate_and_report(metric_name, metric_value)
        return self.exporter.export_json_report(output_path)

    def log_bridge_anomaly(self, source, severity, details, snapshot):
        """Передает снимок телеметрии в hub."""
        self.hub.log_anomaly(source, severity, details, snapshot)

    def transfer_to_json(self, output_path):
        """Интеграционный метод для передачи данных из hub в exporter."""
        # Получаем данные из хаба
        data = self.hub.generate_final_report()

        # Если данные не являются списком, приводим к формату для экспорта
        if not isinstance(data, list):
            data = [data] if data else []

        normalized_data = []
        for entry in data:
            if isinstance(entry, dict):
                norm_entry = entry.copy()
                details = norm_entry.get("details")
                if isinstance(details, dict):
                    if "metric_name" in details and "metric_name" not in norm_entry:
                        norm_entry["metric_name"] = details["metric_name"]
                    if "value" in details and "value" not in norm_entry:
                        norm_entry["value"] = details["value"]
                normalized_data.append(norm_entry)
            else:
                normalized_data.append(entry)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, ensure_ascii=False, indent=4)

        return output_path