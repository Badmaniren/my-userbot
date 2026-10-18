from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_filter import AnomalyFilter, start_new


class AnomalySecurityGatewayError(Exception):
    """Кастомное исключение для ошибок шлюза безопасности аномалий."""
    pass


class AnomalySecurityGateway:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.audit_hub = AnomalyAuditHub(repo_path, log_path, threshold)
        self.filter_engine = AnomalyFilter()
        self.filter_module = self.filter_engine

    def process_and_secure_anomaly(self, raw_input_data: dict) -> dict:
        try:
            try:
                filtered_result = self.filter_engine.filter(raw_input_data)
            except Exception:
                safe_data = dict(raw_input_data)
                required_keys = ["source", "severity", "details", "telemetry_snapshot"]
                for key in required_keys:
                    if key not in safe_data:
                        safe_data[key] = {} if key == "telemetry_snapshot" else f"default_{key}"
                filtered_result = self.filter_engine.filter(safe_data)

            source = raw_input_data.get("source")
            severity = raw_input_data.get("severity")
            details = raw_input_data.get("details")
            telemetry_snapshot = raw_input_data.get("telemetry_snapshot", {})

            self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)

            metric = raw_input_data.get("metric")
            metric_value = raw_input_data.get("metric_value")
            if metric is not None and metric_value is not None:
                self.audit_hub.aggregate_and_report(metric, metric_value)

            return filtered_result
        except Exception as e:
            if isinstance(e, AnomalySecurityGatewayError):
                raise
            raise AnomalySecurityGatewayError(str(e)) from e

    def ingest_raw_stream(self, data_chunk):
        return start_new(data_chunk)

    def process_and_filter(self, raw_data: dict) -> dict:
        try:
            return self.filter_engine.filter(raw_data)
        except Exception:
            safe_data = dict(raw_data)
            required_keys = ["id", "source", "severity", "details", "metric", "telemetry_snapshot"]
            for key in required_keys:
                if key not in safe_data:
                    safe_data[key] = {} if key == "telemetry_snapshot" else f"default_{key}"
            return self.filter_engine.filter(safe_data)
