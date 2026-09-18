import os
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.incident_aggregator import IncidentAggregator
from skills.telemetry_streamer import telemetry_streamer
from skills.incident_aggregator import incident_aggregator
from skills.telemetry_anomaly_evaluator_core import telemetry_anomaly_evaluator_core
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.incident_notification_bridge import incident_notification_bridge
from skills.extractor_tool_1789544538 import extractor_tool_1789544538


class IncidentForensicLogger:
    def log_incident_traces(self, incident, output_path):
        data_to_write = ""
        if isinstance(incident, dict):
            data_to_write = json.dumps(incident)
        else:
            data_to_write = str(incident)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data_to_write)
        return True


def start_new(*args, **kwargs):
    incident_id = kwargs.get("incident_id") or kwargs.get("target_id")
    stream = kwargs.get("stream")
    telemetry_data = kwargs.get("telemetry_data")
    telemetry_channel = kwargs.get("telemetry_channel") or kwargs.get("source")
    bridge_target = kwargs.get("bridge_target")
    artifact_path = kwargs.get("artifact_path")

    target_id = kwargs.get("target_id")

    if stream is not None:
        telemetry_streamer(stream)
        incident_aggregator.aggregate(incident_id=incident_id, stream=stream)

    if telemetry_data is not None:
        telemetry_anomaly_evaluator_core.evaluate(telemetry_data)

    if telemetry_channel is not None or target_id is not None:
        system_health_telemetry_collector.collect(channel=telemetry_channel, target_id=target_id)

    if bridge_target is not None:
        incident_notification_bridge.dispatch(target=bridge_target, incident_id=incident_id)

    if artifact_path is not None:
        extractor_tool_1789544538.extract(path=artifact_path)

    return incident_id or "OK"