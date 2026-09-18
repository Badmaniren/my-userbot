import os
import uuid
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills import incident_severity_evaluator

def incident_forensic_summarizer(incident_data=None, include_telemetry_dump=True):
    if incident_data is None:
        incident_data = {}
    
    target_id = incident_data.get("incident_id", f"inc-{uuid.uuid4()}")
    telemetry = incident_data.get("telemetry_payload", {})
    
    dump_str = str(telemetry) if include_telemetry_dump else ""
    summary_id = f"sum-{uuid.uuid4()}"
    
    report_filename = f"report_{summary_id}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"Incident ID: {target_id}\n")
        f.write(f"Telemetry Dump: {dump_str}\n")
        
    return {
        "summary_id": summary_id,
        "target_incident_id": target_id,
        "telemetry_dump": dump_str,
        "report_file_path": report_filename
    }

def start_new(*args, **kwargs):
    if "faulty_param" in kwargs:
        incident_severity_evaluator.evaluate(kwargs["faulty_param"])
        
    incident_id = kwargs.get("incident_id")
    if not incident_id and len(args) > 0:
        incident_id = args[0]
    if not incident_id:
        incident_id = f"INC-{uuid.uuid4()}"
        
    telemetry_source = kwargs.get("telemetry_source") or kwargs.get("stream")
    if not telemetry_source and len(args) > 1:
        telemetry_source = args[1]
        
    telemetry_data = {}
    if telemetry_source and hasattr(telemetry_source, "read"):
        telemetry_data = {"raw": telemetry_source.read().decode('utf-8', errors='ignore')}
        
    incident_payload = incident_aggregator(
        incident_id=incident_id,
        telemetry_payload=telemetry_data,
        severity_level="CRITICAL"
    )
    
    result = incident_forensic_summarizer(
        incident_data=incident_payload,
        include_telemetry_dump=True
    )
    
    if isinstance(result, dict) and hasattr(result, "_mock_return_value"):
        return dict(result)
        
    return result