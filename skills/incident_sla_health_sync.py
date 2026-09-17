import io
from skills.incident_sla_tracker import IncidentSLATracker
from skills.system_health_aggregator import SystemHealthAggregator


def sync_sla_with_health(sla_data, aggregator):
    if not isinstance(sla_data, dict):
        raise ValueError("Invalid SLA data")
    return {
        "status": "synchronized",
        "token": sla_data.get("token"),
        "health_score": aggregator(),
    }


def process_sla_stream(stream):
    content = stream.read()
    if not content:
        raise ValueError("Empty stream")
    return len(content)


def external_dispatch(val):
    return val


def execute_sync_pipeline(val):
    return external_dispatch(val)


def validate_and_sync(data):
    if not isinstance(data, dict) or "id" not in data:
        raise TypeError("Malformed payload")
    return True


def sync_sla_to_health_aggregator(test_payload):
    incident_id = test_payload.get("incident_id")
    sla_status = test_payload.get("sla_status")
    impact_score = test_payload.get("impact_score")

    sla_tracker = IncidentSLATracker()
    health_aggregator = SystemHealthAggregator()

    sla_tracker.save_incident_data(incident_id, {"status": sla_status})
    health_aggregator.update_system_health(
        incident_id, {"impact_score": impact_score}
    )

    return {"success": True, "incident_id": incident_id}