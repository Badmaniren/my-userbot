import hashlib
import io
import os

class AnomalyEvaluationException(Exception):
    """Custom exception for anomaly evaluation failures."""
    pass

class InvalidTelemetryStreamException(Exception):
    """Custom exception for invalid telemetry data structure."""
    pass

class TelemetryAnomalyEvaluatorCore:
    def _internal_processor(self, data):
        # Core logic for processing
        return data

    def _read_stream_bytes(self, stream):
        return stream.read()

    def evaluate(self, telemetry_data):
        if not all(k in telemetry_data for k in ("stream_id", "metric", "value", "threshold")):
            raise InvalidTelemetryStreamException("Missing required telemetry fields")
        
        try:
            self._internal_processor(telemetry_data)
            is_anomaly = telemetry_data["value"] > telemetry_data["threshold"]
            return {
                "is_anomaly": is_anomaly,
                "stream_id": telemetry_data["stream_id"],
                "deviation": max(0.0, telemetry_data["value"] - telemetry_data["threshold"]) if is_anomaly else 0.0
            }
        except Exception as e:
            raise AnomalyEvaluationException(str(e))

    def evaluate_stream_source(self, stream_io):
        content = self._read_stream_bytes(stream_io)
        return {
            "processed_bytes_hash": hashlib.sha256(content).hexdigest()
        }

    def evaluate_with_incident_trigger(self, telemetry_payload):
        result = self.evaluate(telemetry_payload)
        return {
            "incident_triggered": result["is_anomaly"],
            "trigger_id": telemetry_payload.get("trigger_id"),
            "evaluated_stream": telemetry_payload["stream_id"]
        }

# Integration dependencies (Mocking imports as per instructions: 
# if they don't exist, they will raise ImportError naturally)
from skills.telemetry_anomaly_evaluator_core import (
    auto_patch_pipeline,
    dependency_audit_reporter,
    error_recovery_hub,
    extractor_tool_1789544538,
    incident_aggregator,
    incident_auto_escalation_engine,
    incident_auto_recovery_dispatcher,
    incident_business_loss_reporter,
    incident_financial_impact_evaluator,
    incident_impact_analyzer,
    incident_knowledge_base_searcher,
    incident_notification_bridge,
    incident_notification_broadcaster,
    incident_post_mortem_service,
    incident_severity_evaluator,
    incident_sla_breach_predictor,
    incident_sla_mitigation_planner,
    incident_sla_recovery_coordinator,
    incident_sla_tracker,
    incident_trend_analyzer,
    incident_trend_forecaster,
    notification_channel_dispatcher,
    notification_template_engine,
    notification_webhook_broadcaster,
    package_requirement_reader,
    patch_auto_executor,
    patch_metric_collector,
    patch_scheduler,
    patch_validator,
    preventive_patch_applier,
    pypi_client,
    recovery_dashboard_generator,
    recovery_report_exporter,
    system_health_aggregator,
    system_health_audit_pipeline,
    system_health_monitoring_gateway,
    system_health_reporter,
    system_health_telemetry_collector,
    telemetry_processor,
    telemetry_streamer,
    vulnerability_scanner
)