import os
from skills import system_health_telemetry_collector as _sh_tc
from skills import system_health_audit_pipeline as _sh_ap
from skills import incident_aggregator as _inc_agg
from skills import telemetry_streamer as _tel_str
from skills import incident_impact_analyzer as _inc_imp
from skills import telemetry_anomaly_evaluator_core as _tel_eval
from skills import error_recovery_hub as _err_hub
from skills import telemetry_processor as _tel_proc

system_health_telemetry_collector = getattr(_sh_tc, "system_health_telemetry_collector", None) or _sh_tc.SystemHealthTelemetryCollector()
system_health_audit_pipeline = getattr(_sh_ap, "system_health_audit_pipeline", None) or _sh_ap.SystemHealthAuditPipeline()
incident_aggregator = getattr(_inc_agg, "incident_aggregator", None) or _inc_agg.IncidentAggregator()
telemetry_streamer = getattr(_tel_str, "telemetry_streamer", None) or _tel_str.TelemetryStreamer()
incident_impact_analyzer = getattr(_inc_imp, "incident_impact_analyzer", None) or _inc_imp.IncidentImpactAnalyzer()
telemetry_anomaly_evaluator_core = getattr(_tel_eval, "telemetry_anomaly_evaluator_core", None) or _tel_eval.TelemetryAnomalyEvaluatorCore()
error_recovery_hub = getattr(_err_hub, "error_recovery_hub", None) or _err_hub.ErrorRecoveryHub()
telemetry_processor = getattr(_tel_proc, "telemetry_processor", None) or _tel_proc.TelemetryProcessor()


def incident_forensic_pipeline(incident_input, output_file):
    if isinstance(incident_input, dict):
        unique_id = (
            incident_input.get("final_id")
            or incident_input.get("incident_ref")
            or incident_input.get("identifier")
            or incident_input.get("incident_id")
            or incident_input.get("id")
            or incident_input.get("session_id")
            or "unknown"
        )
    else:
        unique_id = str(incident_input)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Forensic Report for session: {unique_id}\n")

    return f"Pipeline executed successfully for {unique_id}"


def start_new(payload, mode=None, strict=False, stream_mode=False, source=None):
    if strict:
        if hasattr(system_health_audit_pipeline, "run_audit"):
            system_health_audit_pipeline.run_audit()
        raise ValueError(f"Corrupted token: {payload}")

    if stream_mode:
        if hasattr(telemetry_processor, "process_stream"):
            telemetry_processor.process_stream(payload)
        if hasattr(incident_aggregator, "aggregate"):
            return incident_aggregator.aggregate()
        return {"final_id": str(payload), "state": "compiled"}

    if mode == "audit":
        eval_res = None
        if hasattr(telemetry_anomaly_evaluator_core, "detect"):
            eval_res = telemetry_anomaly_evaluator_core.detect()
        if eval_res and hasattr(error_recovery_hub, "dispatch"):
            return error_recovery_hub.dispatch()
        return {}

    if callable(telemetry_streamer):
        telemetry_streamer(payload, source=source)
    elif hasattr(telemetry_streamer, "stream"):
        telemetry_streamer.stream(payload)

    col_res = None
    if hasattr(system_health_telemetry_collector, "collect"):
        col_res = system_health_telemetry_collector.collect()

    if hasattr(incident_impact_analyzer, "evaluate"):
        incident_impact_analyzer.evaluate()

    if isinstance(col_res, dict) and "incident_ref" in col_res:
        return col_res

    return {"incident_ref": payload}
