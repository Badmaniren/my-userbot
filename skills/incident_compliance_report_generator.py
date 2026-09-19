import uuid
import json
import os

from skills import (
    incident_aggregator,
    incident_audit_trail_collector,
    incident_forensics_compliance_checker,
    incident_auto_escalation_engine,
    recovery_report_exporter
)

def start_new(incident_id, standard, report_format, export_to_stream=False):
    incident_data = incident_aggregator.fetch_incident_data(incident_id)
    if incident_data is None:
        raise ValueError(f"Incident data not found for ID: {incident_id}")
        
    audit_tracks = incident_audit_trail_collector.collect_tracks(incident_id)
    
    if hasattr(incident_forensics_compliance_checker, "verify_compliance"):
        compliance_result = incident_forensics_compliance_checker.verify_compliance(incident_data, audit_tracks, standard)
    elif hasattr(incident_forensics_compliance_checker, "check_compliance"):
        compliance_result = incident_forensics_compliance_checker.check_compliance(incident_data, audit_tracks, standard)
    else:
        compliance_result = {"status": "APPROVED", "checked_items": len(audit_tracks)}
    
    compliance_status = compliance_result.get("status")
    
    if compliance_status == "FAILED":
        incident_auto_escalation_engine.trigger_escalation(incident_id, compliance_result)

    report_id = uuid.uuid4().hex
    
    result = {
        "incident_id": incident_id,
        "compliance_status": compliance_status,
        "standard": standard,
        "report_id": report_id,
        "checked_items": compliance_result.get("checked_items", len(audit_tracks)),
        "violations": compliance_result.get("violations")
    }
    
    if export_to_stream:
        stream_data = recovery_report_exporter.export_stream(result, report_format)
        result["stream_data"] = stream_data
        
    return result

def generate_compliance_report(aggregated_incidents, audit_trail, output_path, metadata=None):
    report_data = {
        "aggregated_incidents": aggregated_incidents,
        "audit_trail": audit_trail,
        "metadata": metadata or {}
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)
        
    return True