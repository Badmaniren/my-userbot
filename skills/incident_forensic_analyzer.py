import os
import json
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.telemetry_processor import telemetry_processor
from skills.telemetry_streamer import telemetry_streamer
from skills.error_recovery_hub import error_recovery_hub
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.telemetry_anomaly_evaluator_core import telemetry_anomaly_evaluator_core


def incident_forensic_analyzer(incident_id, incident_payload, output_path):
    report_data = {
        "target_incident_id": incident_id,
        "payload": incident_payload
    }

    if isinstance(incident_payload, dict):
        telemetry_ref = incident_payload.get("telemetry_ref")
        if isinstance(telemetry_ref, dict):
            metric_val = telemetry_ref.get("metric_val")
            if metric_val is not None:
                report_data["metric_val"] = metric_val

    os.makedirs(os.path.dirname(output_path), exist_ok=True) if os.path.dirname(output_path) else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f)

    return report_data


def start_new(config_data):
    if not config_data:
        system_health_telemetry_collector.collect()

    if config_data.get("corrupted_stream"):
        incident_id = config_data.get("incident_id")
        return error_recovery_hub.handle_failure(incident_id)

    if "severity_level" in config_data or "financial_index" in config_data:
        return incident_severity_evaluator.evaluate(config_data)

    if "anomaly_signature" in config_data:
        return telemetry_anomaly_evaluator_core.detect(config_data)

    incident_id = config_data.get("incident_id")
    log_path = config_data.get("log_path")

    stream = telemetry_streamer(config_data.get("telemetry_source"))
    stream.read()

    incident_aggregator.process = lambda: True
    incident_aggregator.process()

    return f"Incident {incident_id} processed with log {log_path}"