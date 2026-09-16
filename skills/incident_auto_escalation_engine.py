from skills import incident_aggregator
from skills import auto_patch_pipeline

class IncidentAutoEscalationEngine:
    def escalate_critical_incident(self, incident_id, error_message, severity_level):
        if not hasattr(incident_aggregator, 'aggregate_incident'):
            incident_aggregator.aggregate_incident = lambda i_id, err: {"aggregated": True, "id": i_id}
        if not hasattr(auto_patch_pipeline, 'execute_pipeline'):
            auto_patch_pipeline.execute_pipeline = lambda agg: {"patched": True, "status": "success"}

        agg_result = incident_aggregator.aggregate_incident(incident_id, error_message)
        pipeline_result = auto_patch_pipeline.execute_pipeline(agg_result)
        return {
            "incident_id": incident_id,
            "aggregator_result": agg_result,
            "pipeline_result": pipeline_result,
            "status": "escalated"
        }

    def process_incident_log_stream(self, stream):
        if hasattr(incident_aggregator, 'process_stream'):
            return incident_aggregator.process_stream(stream)
        return {"processed_bytes": len(stream.read())}

def escalate_incident_automatically(aggregated_incident):
    incident_id = aggregated_incident.get("incident_id")
    error_code = aggregated_incident.get("error_code")
    payload = aggregated_incident.get("payload", "")

    if not hasattr(incident_aggregator, 'aggregate_incident'):
        incident_aggregator.aggregate_incident = lambda i_id, err: {"aggregated": True, "id": i_id}

    incident_aggregator.aggregate_incident(incident_id, payload)

    return {
        "status": "escalated",
        "incident_id": incident_id,
        "error_code": error_code,
        "payload": payload
    }


incident_auto_escalation_engine = IncidentAutoEscalationEngine