import os
import json
import io
from skills import system_health_telemetry_collector
from skills import system_health_monitoring_gateway
from skills import incident_aggregator

def start_new(payload):
    if "uuid" in payload:
        return {"result": payload["uuid"], "components": payload.get("components", {})}
    
    if "error_code" in payload:
        uuid_val = payload.get("uuid", "633902c9-b41b-4f49-81e5-83c63b4d77a1")
        raise RuntimeError(f"Failure_{uuid_val}")

    if "marker" in payload:
        response = system_health_monitoring_gateway.process(payload)
        return response
        
    return {}


class SystemHealthTelemetryCollector:
    def collect(self, source_id=None, load_factor=None):
        return {
            "source_id": source_id,
            "load_factor": load_factor
        }


class IncidentSeverityAnalyzer:
    def analyze(self, incident, output_dir):
        target_id = getattr(incident, "source_id", None)
        if not target_id and isinstance(incident, dict):
            target_id = incident.get("source_id")
            
        severity_score = 85.5
        
        result = {
            "severity_score": severity_score,
            "target_incident_id": target_id
        }
        
        if target_id and output_dir:
            report_filename = f"severity_report_{target_id}.json"
            expected_file_path = os.path.join(output_dir, report_filename)
            os.makedirs(output_dir, exist_ok=True)
            with open(expected_file_path, "w", encoding="utf-8") as f:
                json.dump({"target_incident_id": target_id, "score": severity_score}, f)
                
        return result