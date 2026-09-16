import os
import json
from skills import (
    incident_severity_evaluator,
    incident_aggregator,
    notification_channel_dispatcher,
    incident_notification_broadcaster,
    system_health_telemetry_collector,
    incident_trend_analyzer,
    vulnerability_scanner,
    auto_patch_pipeline
)

class IncidentAutoEscalationEngine:
    def process_escalation(self, incident_id: str) -> dict:
        incident = incident_aggregator.get_incident(incident_id)
        sev_score = incident_severity_evaluator.evaluate(incident)

        if sev_score <= 0:
            return {
                "incident_id": incident_id,
                "severity": sev_score,
                "skipped": True
            }

        channel = notification_channel_dispatcher.dispatch(incident)
        broadcast_incident_notification = incident_notification_broadcaster.broadcast(incident)

        return {
            "incident_id": incident_id,
            "severity": sev_score,
            "escalated_to": channel,
            "channel": channel,
            "broadcast_success": broadcast_incident_notification
        }

    def evaluate_system_telemetry_risks(self) -> dict:
        telemetry_data = system_health_telemetry_collector.collect()
        metric_key, metric_val = next(iter(telemetry_data.items()))
        trend_report = incident_trend_analyzer.analyze(telemetry_data)
        
        trend_report["risk_metric"] = metric_val
        return trend_report

    def check_and_trigger_patching(self) -> bool:
        vulnerabilities = vulnerability_scanner.scan()
        if vulnerabilities:
            return auto_patch_pipeline.auto_patch_pipeline(vulnerabilities)
        return False

    def consume_stream_data(self) -> bytes:
        stream = incident_aggregator.stream_raw_data()
        return stream.read()


def auto_escalate_incident(incident_id: str, severity: int, workspace_dir: str) -> dict:
    escalation_result = {
        "escalated_incident_id": incident_id,
        "status": "SUCCESS",
        "severity": severity
    }
    
    file_path = os.path.join(workspace_dir, f"escalated_{incident_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(escalation_result, f)
        
    return escalation_result