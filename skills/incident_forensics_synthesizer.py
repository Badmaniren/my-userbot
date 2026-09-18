from skills import incident_audit_trail_collector
from skills import incident_aggregator


class IncidentForensicsSynthesizer:
    def synthesize(self, module_name, exception, traceback_str, incident_id):
        return incident_aggregator.aggregate_incidents(module_name, exception, traceback_str)


def synthesize_forensics_report(
    module_name,
    exception=None,
    traceback_str="",
    incident_id=None,
    destination_path=None,
    include_raw_telemetry=True,
    incident_data=None,
    exception_obj=None
):
    actual_exception = exception if exception is not None else exception_obj
    if actual_exception is None:
        actual_exception = Exception("Unknown error")

    if incident_data is None:
        incident_data = {
            "id": incident_id,
            "module": module_name,
            "error": str(actual_exception)
        }

    agg_result = incident_aggregator.aggregate_incidents(
        module_name, actual_exception, traceback_str
    )

    trail_path = incident_audit_trail_collector.collect_incident_audit_trail(
        incident_data, destination_path, include_raw_telemetry
    )

    if destination_path and not trail_path:
        import json
        import os
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
        with open(destination_path, "w", encoding="utf-8") as f:
            json.dump(incident_data, f)
        trail_path = destination_path

    return {
        "incident_id": incident_id or incident_data.get("id"),
        "aggregation_result": agg_result,
        "audit_trail_path": trail_path
    }