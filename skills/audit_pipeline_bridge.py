from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_pipeline import AnomalyPipeline


class AuditPipelineBridgeError(Exception):
    """Кастомное исключение для ошибок конвейера аудита."""
    pass


class AuditPipelineBridge:
    """
    Мост, связывающий anomaly_audit_hub и anomaly_pipeline
    для автоматического запуска проверок безопасности в едином конвейере.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        # Для интеграционного теста, обращающегося к self.bridge.audit_hub:
        self.audit_hub = self.hub

        self.pipeline = AnomalyPipeline(
            repo_path=self.repo_path,
            threshold=self.threshold
        )

    def run_audit_pipeline(self, raw_input_data):
        try:
            result = self.pipeline.run(raw_input_data)
            self.hub.aggregate_and_report()
            return result
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Pipeline failure: {e}") from e

    def execute_batch_audit(self, raw_batch):
        try:
            res = self.pipeline.run_batch(raw_batch)
            self.hub.generate_final_report()
            return res
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Batch error: {e}") from e

    def log_external_anomaly(self, source, severity, details, telemetry_snapshot):
        try:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Log external anomaly failure: {e}") from e

    def run_full_security_cycle(self, execution_id, metrics_payload):
        try:
            res = self.pipeline.run_end_to_end(execution_id, metrics_payload)
            self.hub.generate_final_report()
            return res
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Full security cycle failure: {e}") from e

    def process_stream_data(self, stream_data):
        try:
            return self.pipeline.process_pipeline(stream_data)
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Stream data processing failure: {e}") from e

    def run_security_audit_pipeline(self, execution_id, metrics_payload, raw_input_data):
        try:
            if raw_input_data:
                self.hub.log_anomaly(
                    source=raw_input_data.get("source"),
                    severity=raw_input_data.get("severity"),
                    details=raw_input_data.get("details"),
                    telemetry_snapshot=raw_input_data.get("telemetry_snapshot")
                )
            return self.pipeline.run_end_to_end(execution_id, metrics_payload)
        except Exception as e:
            if isinstance(e, AuditPipelineBridgeError):
                raise
            raise AuditPipelineBridgeError(f"Security audit pipeline failure: {e}") from e