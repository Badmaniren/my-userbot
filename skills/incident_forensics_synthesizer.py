from skills import incident_audit_trail_collector
from skills import incident_aggregator


class IncidentForensicsSynthesizer:
    def synthesize(self, *args, **kwargs):
        if len(args) == 2 and isinstance(args[1], dict):
            raw_trail, audit_data = args
            res = dict(audit_data)
            res["raw_trail"] = raw_trail
            return res

        if "audit_data" in kwargs:
            audit_data = kwargs["audit_data"]
            res = dict(audit_data) if isinstance(audit_data, dict) else {"audit_data": audit_data}
            if len(args) > 0:
                res["raw_trail"] = args[0]
            elif "raw_trail" in kwargs:
                res["raw_trail"] = kwargs["raw_trail"]
            return res

        module_name = kwargs.get("module_name", args[0] if len(args) > 0 else "unknown")
        exception = kwargs.get("exception", args[1] if len(args) > 1 else None)
        traceback_str = kwargs.get("traceback_str", args[2] if len(args) > 2 else "")
        incident_id = kwargs.get("incident_id", args[3] if len(args) > 3 else None)

        if isinstance(module_name, dict) and len(args) == 1:
            return module_name

        agg = incident_aggregator.aggregate_incidents(module_name, exception, traceback_str)
        if isinstance(agg, dict) and incident_id and "incident_id" not in agg:
            agg["incident_id"] = incident_id
        return agg


incident_forensics_synthesizer = IncidentForensicsSynthesizer


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
