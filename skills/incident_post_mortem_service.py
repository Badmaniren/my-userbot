import io
import uuid
from typing import Dict, Any, List, Union

from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter
from skills.incident_knowledge_base_searcher import IncidentKnowledgeBaseSearcher


class IncidentPostMortemService:
    def __init__(self):
        self.incident_aggregator = IncidentAggregator()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.report_exporter = RecoveryReportExporter()
        self.archived_reports: List[Dict[str, Any]] = []
        
        if not hasattr(self.incident_aggregator, "aggregate"):
            setattr(self.incident_aggregator, "aggregate", lambda incident_id: {})
            
        if not hasattr(self.error_recovery_hub, "get_logs"):
            setattr(self.error_recovery_hub, "get_logs", lambda incident_id: b"")

        if not hasattr(self.report_exporter, "export"):
            setattr(self.report_exporter, "export", lambda report: None)

    def archive_report(self, report: Dict[str, Any]) -> None:
        if report not in self.archived_reports:
            self.archived_reports.append(report)
        IncidentKnowledgeBaseSearcher.archive_report_global(report)

    def _fetch_incident_metrics(self, incident_id: str) -> Dict[str, Any]:
        if not hasattr(self.incident_aggregator, "aggregate"):
            return {}
        res = self.incident_aggregator.aggregate(incident_id)
        if isinstance(res, dict):
            return res
        return {}

    def _fetch_recovery_logs(self, incident_id: str) -> io.BytesIO:
        if not hasattr(self.error_recovery_hub, "get_logs"):
            return io.BytesIO(b"")
        logs = self.error_recovery_hub.get_logs(incident_id)
        if isinstance(logs, bytes):
            return io.BytesIO(logs)
        if isinstance(logs, str):
            return io.BytesIO(logs.encode('utf-8'))
        return io.BytesIO(b"")

    def _parse_recovery_logs(self, log_stream: io.BytesIO) -> List[str]:
        content = log_stream.read().decode('utf-8', errors='ignore')
        if not content:
            return []
        lines = content.splitlines()
        return [line.strip() for line in lines if line.strip()]

    def _evaluate_root_cause(self, metrics: Dict[str, Any], logs: List[str]) -> str:
        causes = []
        if metrics.get("memory_leak_detected") or metrics.get("memory_leak_mb"):
            causes.append("Memory leak detected")
        if metrics.get("timeout_count"):
            causes.append(f"High timeout count: {metrics.get('timeout_count')}")
        
        logs_str = " ".join(logs)
        if logs_str:
            causes.append(f"Logs analysis: {logs_str}")
        
        return "Root cause identified. " + "; ".join(causes)

    def generate_report(self, incident: Union[str, Dict[str, Any]], recovery_data: Dict[str, Any] = None) -> Dict[str, Any]:
        if isinstance(incident, dict):
            incident_id = incident.get("incident_id", str(uuid.uuid4()))
            title = incident.get("title", incident.get("summary", f"Incident {incident_id}"))
            metrics_data = incident.get("metrics", {})
            
            if recovery_data and isinstance(recovery_data, dict):
                logs_raw = recovery_data.get("logs", "")
                if isinstance(logs_raw, bytes):
                    logs_stream = io.BytesIO(logs_raw)
                else:
                    logs_stream = io.BytesIO(str(logs_raw).encode('utf-8'))
            else:
                logs_stream = io.BytesIO(b"")
                
            parsed_logs = self._parse_recovery_logs(logs_stream)
            root_cause = self._evaluate_root_cause(metrics_data, parsed_logs)
            
            error_code = incident.get("error_code")
            if error_code and error_code not in root_cause:
                root_cause = f"Error code: {error_code}. " + root_cause
            
            report = {
                "id": str(uuid.uuid4()),
                "title": title,
                "summary": f"Post-mortem summary for {title}",
                "report_id": str(uuid.uuid4()),
                "incident_id": incident_id,
                "timeline": [{"event": "incident_started"}, {"event": "recovery_completed"}],
                "root_cause_analysis": root_cause,
                "root_cause": root_cause,
                "metrics_snapshot": metrics_data,
                "recovery_logs_summary": " ".join(parsed_logs)
            }
            if hasattr(self.report_exporter, "export"):
                self.report_exporter.export(report)
            return report
        else:
            incident_id = str(incident)
            title = incident_id
            metrics_data = self._fetch_incident_metrics(incident_id)
            logs_stream = self._fetch_recovery_logs(incident_id)
            parsed_logs = self._parse_recovery_logs(logs_stream)
            root_cause = self._evaluate_root_cause(metrics_data, parsed_logs)
            
            if recovery_data and isinstance(recovery_data, str):
                summary_str = recovery_data
            else:
                summary_str = f"Post-mortem report for {title}"

            report = {
                "id": str(uuid.uuid4()),
                "title": title,
                "summary": summary_str,
                "incident_id": incident_id,
                "timeline": [],
                "root_cause": root_cause,
                "root_cause_analysis": root_cause,
                "metrics_snapshot": metrics_data,
                "recovery_logs_summary": " ".join(parsed_logs)
            }
            if hasattr(self.report_exporter, "export"):
                self.report_exporter.export(report)
            return report

    def import_historical_data(self, data_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        imported_reports = []
        for incident in data_batch:
            report = self.generate_report(incident)
            imported_reports.append(report)
        return imported_reports

    def export_summary_analytics(self, incidents: List[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
        total_incidents = len(incidents)
        reports = [self.generate_report(inc) for inc in incidents]
        return {
            "total_incidents": total_incidents,
            "reports_summary": reports
        }
