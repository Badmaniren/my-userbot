import json
import os
import requests
from skills.incident_aggregator import incident_aggregator
from skills.telemetry_processor import telemetry_processor
from skills.telemetry_streamer import telemetry_streamer
from skills.telemetry_anomaly_evaluator_core import telemetry_anomaly_evaluator_core
from skills.incident_severity_evaluator import incident_severity_evaluator

def start_new(incident_id, telemetry_source, evaluate_anomalies=False):
    logs = incident_aggregator()
    
    try:
        telemetry_streamer(telemetry_source)
    except FileNotFoundError:
        raise

    try:
        telemetry_processor(telemetry_source)
    except Exception as e:
        raise e

    anomaly_score = None
    severity = None

    if evaluate_anomalies:
        anomaly_res = telemetry_anomaly_evaluator_core()
        anomaly_score = anomaly_res.get("anomaly_score")
        severity = incident_severity_evaluator()

    payload = {
        "incident_id": incident_id,
        "telemetry_source": telemetry_source,
        "logs": logs
    }
    payload.update(logs)

    response = requests.post("https://example.com/api/incident", json=payload)
    
    result = response.json()
    if anomaly_score is not None:
        result["anomaly_score"] = anomaly_score
    if severity is not None:
        result["severity"] = severity

    return result

def incident_forensic_reporter(config):
    incident_data = config.get("incident_data", {})
    output_path = config.get("output_path")
    
    target_incident_id = incident_data.get("incident_id")
    
    report = {
        "report_status": "SUCCESS",
        "target_incident_id": target_incident_id,
        "details": incident_data
    }
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
    return report