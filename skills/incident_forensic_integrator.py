import io
import os
import tempfile

from skills import (
    incident_aggregator,
    incident_impact_analyzer,
    incident_severity_evaluator,
    system_health_telemetry_collector,
    telemetry_processor,
    telemetry_streamer,
)


def start_new(
    incident_id=None,
    telemetry_source=None,
    error_code=None,
    stream_token=None,
    incident_uuid=None,
    deep_inspection=False,
):
    target_incident_id = incident_id or incident_uuid
    if not target_incident_id or target_incident_id == "":
        raise ValueError("Invalid identifier")

    telemetry_payload = None
    if stream_token is not None:
        stream_obj = telemetry_streamer.stream(token=stream_token)
        telemetry_payload = telemetry_processor.process(stream_obj)
    elif telemetry_source is not None:
        telemetry_payload = telemetry_processor.process(telemetry_source)
    else:
        telemetry_payload = io.BytesIO(b"default_payload")

    aggregated_data = incident_aggregator.aggregate(
        incident_id=target_incident_id,
        telemetry_payload=telemetry_payload
    )

    if not isinstance(aggregated_data, dict):
        aggregated_data = {"data": aggregated_data}

    if "incident_id" not in aggregated_data:
        aggregated_data["incident_id"] = target_incident_id

    if deep_inspection:
        severity = incident_severity_evaluator.evaluate(target_incident_id)
        aggregated_data["severity"] = severity

    return aggregated_data