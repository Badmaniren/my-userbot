from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class DigestAuditPipelineError(Exception):
    """Исключение, возникающее при ошибках в пайплайне аудита."""
    pass


class DigestAuditPipeline:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None, output_json_path=None, output_html_path=None):
        if audit_hub is not None:
            self.audit_hub = audit_hub
            self.audit_hub.repo_path = repo_path
            self.audit_hub.log_path = log_path
            self.audit_hub.threshold = threshold
        else:
            hub_repo_path = repo_path if repo_path is not None else "."
            hub_log_path = log_path if log_path is not None else "/tmp/anomaly_audit.log"
            hub_threshold = threshold if threshold is not None else 0.5
            self.audit_hub = AnomalyAuditHub(
                repo_path=hub_repo_path,
                log_path=hub_log_path,
                threshold=hub_threshold
            )
            self.audit_hub.repo_path = hub_repo_path
            self.audit_hub.log_path = hub_log_path
            self.audit_hub.threshold = hub_threshold

        self.output_json_path = output_json_path
        self.output_html_path = output_html_path
        self.exporter = DigestExporter(self.audit_hub)

    def run_audit_and_export_json(
        self,
        output_path=None,
        source=None,
        severity=None,
        details=None,
        telemetry_snapshot=None,
        metric_name=None,
        metric_value=None,
        value=None
    ):
        actual_metric_value = metric_value if metric_value is not None else value
        try:
            if source is not None or severity is not None or details is not None or telemetry_snapshot is not None:
                self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)

            if metric_name is not None and actual_metric_value is not None:
                try:
                    self.audit_hub.aggregate_and_report(metric_name, actual_metric_value)
                except TypeError:
                    try:
                        self.audit_hub.aggregate_and_report(metric_name=metric_name, value=actual_metric_value)
                    except AttributeError:
                        if hasattr(self.audit_hub, 'aggregator') and hasattr(self.audit_hub.aggregator, 'aggregate_and_report'):
                            anomaly_dict = {"source": source or "unknown", "severity": severity or "INFO", "details": details}
                            self.audit_hub.aggregator.aggregate_and_report(anomaly_dict, metric_name, actual_metric_value)
                        else:
                            raise
                except AttributeError:
                    if hasattr(self.audit_hub, 'aggregator') and hasattr(self.audit_hub.aggregator, 'aggregate_and_report'):
                        anomaly_dict = {"source": source or "unknown", "severity": severity or "INFO", "details": details}
                        self.audit_hub.aggregator.aggregate_and_report(anomaly_dict, metric_name, actual_metric_value)
                    else:
                        raise

            self.audit_hub.generate_final_report()

            target_path = output_path or self.output_json_path
            return self.exporter.export_json_report(target_path)
        except Exception as e:
            if isinstance(e, DigestAuditPipelineError):
                raise
            raise DigestAuditPipelineError(str(e)) from e

    def run_audit_and_export_html(
        self,
        output_path=None,
        source=None,
        severity=None,
        details=None,
        telemetry_snapshot=None,
        metric_name=None,
        metric_value=None,
        value=None
    ):
        actual_metric_value = metric_value if metric_value is not None else value
        try:
            if source is not None or severity is not None or details is not None or telemetry_snapshot is not None:
                self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)

            if metric_name is not None and actual_metric_value is not None:
                try:
                    self.audit_hub.aggregate_and_report(metric_name, actual_metric_value)
                except TypeError:
                    try:
                        self.audit_hub.aggregate_and_report(metric_name=metric_name, value=actual_metric_value)
                    except AttributeError:
                        if hasattr(self.audit_hub, 'aggregator') and hasattr(self.audit_hub.aggregator, 'aggregate_and_report'):
                            anomaly_dict = {"source": source or "unknown", "severity": severity or "INFO", "details": details}
                            self.audit_hub.aggregator.aggregate_and_report(anomaly_dict, metric_name, actual_metric_value)
                        else:
                            raise
                except AttributeError:
                    if hasattr(self.audit_hub, 'aggregator') and hasattr(self.audit_hub.aggregator, 'aggregate_and_report'):
                        anomaly_dict = {"source": source or "unknown", "severity": severity or "INFO", "details": details}
                        self.audit_hub.aggregator.aggregate_and_report(anomaly_dict, metric_name, actual_metric_value)
                    else:
                        raise

            self.audit_hub.generate_final_report()

            target_path = output_path or self.output_html_path
            return self.exporter.export_html_report(target_path)
        except Exception as e:
            if isinstance(e, DigestAuditPipelineError):
                raise
            raise DigestAuditPipelineError(str(e)) from e

    def run_audit_and_export(self, *args, **kwargs):
        return self.run_audit_and_export_json(*args, **kwargs)

    def export_comprehensive_json(self, *args, **kwargs):
        return self.run_audit_and_export_json(*args, **kwargs)

    def export_comprehensive_html(self, *args, **kwargs):
        return self.run_audit_and_export_html(*args, **kwargs)

    def run_export_pipeline(self):
        try:
            self.audit_hub.generate_final_report()
            json_res = self.exporter.export_json_report(self.output_json_path)
            html_res = self.exporter.export_html_report(self.output_html_path)
            return json_res, html_res
        except Exception as e:
            if isinstance(e, DigestAuditPipelineError):
                raise
            raise DigestAuditPipelineError(str(e)) from e