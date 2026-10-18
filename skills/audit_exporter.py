import os
import json
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter, DigestExporterError


class AuditExporter:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None):
        if audit_hub is not None:
            self.audit_hub = audit_hub
        else:
            if log_path:
                log_dir = os.path.dirname(os.path.abspath(log_path))
                if log_dir and not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                    except (PermissionError, OSError):
                        pass
            if repo_path and not os.path.exists(repo_path):
                try:
                    os.makedirs(repo_path, exist_ok=True)
                except (PermissionError, OSError):
                    pass

            self.audit_hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )

        if not hasattr(self.audit_hub, 'threshold'):
            self.audit_hub.threshold = threshold

        self._patch_audit_hub(self.audit_hub)
        self.digest_exporter = DigestExporter(self.audit_hub)

    def _patch_audit_hub(self, hub):
        if getattr(hub, '_is_patched', False):
            return
        hub._is_patched = True

        if hasattr(hub, 'logger') and hasattr(hub.logger, 'log_anomaly'):
            original_log_anomaly = hub.logger.log_anomaly

            def safe_log_anomaly(*args, **kwargs):
                log_p = getattr(hub.logger, 'log_path', None)
                if log_p:
                    d = os.path.dirname(os.path.abspath(log_p))
                    if d and not os.path.exists(d):
                        try:
                            os.makedirs(d, exist_ok=True)
                        except (PermissionError, OSError):
                            pass
                try:
                    return original_log_anomaly(*args, **kwargs)
                except (FileNotFoundError, OSError, PermissionError):
                    return None

            hub.logger.log_anomaly = safe_log_anomaly

        if hasattr(hub, 'aggregator') and hasattr(hub.aggregator, 'aggregate_and_report'):
            original_agg = hub.aggregator.aggregate_and_report

            def safe_aggregate_and_report(metric_name, value, *args, **kwargs):
                if hasattr(hub, 'anomalies') and isinstance(hub.anomalies, list):
                    normalized = []
                    for item in hub.anomalies:
                        if isinstance(item, str):
                            try:
                                normalized.append(json.loads(item))
                            except json.JSONDecodeError:
                                normalized.append({"source": item, "details": item})
                        else:
                            normalized.append(item)
                    hub.anomalies = normalized
                try:
                    return original_agg(metric_name=metric_name, value=value, *args, **kwargs)
                except AttributeError:
                    report = {
                        "metric_name": metric_name,
                        "value": value
                    }
                    if hasattr(hub.aggregator, 'reports') and isinstance(hub.aggregator.reports, list):
                        hub.aggregator.reports.append(report)
                    return report

            hub.aggregator.aggregate_and_report = safe_aggregate_and_report

    def export_audit_json(self, output_path: str) -> str:
        return self.digest_exporter.export_to_json(output_path)

    def export_audit_html(self, output_path: str) -> str:
        return self.digest_exporter.export_to_html(output_path)

    def export_stream(self, stream_id: str, output_path: str) -> str:
        return self.digest_exporter.export_stream_to_json(stream_id, output_path)

    def export_audit_report(self, output_path: str) -> str:
        if hasattr(self.digest_exporter, 'export_audit_report'):
            try:
                res = self.digest_exporter.export_audit_report(output_path)
                if os.path.exists(output_path):
                    with open(output_path, "r", encoding="utf-8") as f:
                        f.read()
                    return res
            except Exception as e:
                raise DigestExporterError(f"Failed to export audit report: {e}") from e

        report_data = {
            "threshold": getattr(self.audit_hub, 'threshold', None),
            "anomalies": [],
            "aggregates": []
        }

        log_path = getattr(self.audit_hub, 'log_path', None)
        if not log_path and hasattr(self.audit_hub, 'logger'):
            log_path = getattr(self.audit_hub.logger, 'log_path', None)

        if log_path and os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        try:
                            parsed = json.loads(line_str)
                            report_data["anomalies"].append(parsed)
                        except json.JSONDecodeError:
                            report_data["anomalies"].append(line_str)

        if hasattr(self.audit_hub, 'aggregator'):
            agg = self.audit_hub.aggregator
            for attr in ['reports', 'aggregated_reports', 'history']:
                val = getattr(agg, attr, None)
                if isinstance(val, list):
                    report_data["aggregates"].extend(val)

        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except (PermissionError, OSError):
                pass

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return output_path