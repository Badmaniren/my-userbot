from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()

    def process_and_aggregate(self, module_name, exception, traceback_str, incident_id=None):
        if not incident_id:
            incident_id = self.hub.capture_failure(module_name, exception, traceback_str)
        else:
            if hasattr(self.hub, 'incidents'):
                self.hub.incidents[incident_id] = {
                    "incident_id": incident_id,
                    "module_name": module_name,
                    "error": str(exception) if exception else "Manual escalation",
                    "exception_type": type(exception).__name__ if exception else "Exception",
                    "traceback": traceback_str,
                }
            if hasattr(self.hub, 'history'):
                if module_name not in self.hub.history:
                    self.hub.history[module_name] = []
                self.hub.history[module_name].append({
                    "incident_id": incident_id,
                    "module_name": module_name
                })

        analysis = self.hub.analyze_failure(incident_id) if hasattr(self.hub, 'analyze_failure') else {}
        
        # Записываем метрику
        metric_payload = self.collector.record_metric({
            "incident_id": incident_id,
            "module_name": module_name,
            "success": False,
            "metric_value": 0.0
        })

        metrics_summary = self.collector.get_metrics_summary(module_name)
        history = self.hub.get_incident_history(module_name) if hasattr(self.hub, 'get_incident_history') else []

        return {
            "incident_id": incident_id,
            "module_name": module_name,
            "analysis": analysis,
            "metrics": metric_payload,
            "metrics_summary": metrics_summary,
            "history": history
        }

    def create_ticket(self, incident_data):
        if isinstance(incident_data, dict):
            inc_id = incident_data.get("incident_id") or incident_data.get("id") or "000"
        else:
            inc_id = str(incident_data)
        return f"ticket_{inc_id}"

    def aggregate(self, telemetry=None, incident_tag=None, **kwargs):
        source_id = None
        if isinstance(telemetry, dict):
            source_id = telemetry.get("source_id") or telemetry.get("system_id")
        return {
            "source_id": source_id,
            "incident_tag": incident_tag,
            "telemetry": telemetry,
            "status": "aggregated"
        }


def incident_aggregator(*args, **kwargs):
    aggregator = IncidentAggregator()
    if len(args) == 1 and isinstance(args[0], dict):
        payload = args[0]
        incident_id = payload.get("incident_id") or payload.get("id") or "INC-000"
        system_name = payload.get("system_name") or payload.get("system") or payload.get("module_name") or "default_system"
        severity = payload.get("severity") or "CRITICAL"
    elif len(args) >= 1 and isinstance(args[0], str):
        incident_id = args[0]
        system_name = args[1] if len(args) > 1 and args[1] is not None else kwargs.get("system_name", "default_system")
        severity = args[2] if len(args) > 2 and args[2] is not None else kwargs.get("severity", "CRITICAL")
    elif kwargs:
        incident_id = kwargs.get("incident_id") or kwargs.get("id") or "INC-000"
        system_name = kwargs.get("system_name") or kwargs.get("module_name") or kwargs.get("system") or "default_system"
        severity = kwargs.get("severity", "CRITICAL")
    else:
        return aggregator

    res = aggregator.process_and_aggregate(
        module_name=system_name,
        exception=None,
        traceback_str="",
        incident_id=incident_id
    )
    res.update({
        "id": incident_id,
        "incident_id": incident_id,
        "system": system_name,
        "system_name": system_name,
        "severity": severity,
        "status": "escalated",
        "escalated": True
    })
    return res


def aggregate_incidents(module_name, exception, traceback_str):
    hub = ErrorRecoveryHub()
    collector = PatchMetricCollector()

    incident_id = hub.capture_failure(module_name, exception, traceback_str)
    analysis = hub.analyze_failure(incident_id)
    
    metric_payload = collector.record_metric({
        "incident_id": incident_id,
        "module_name": module_name,
        "success": False,
        "metric_value": 0.0
    })
    metrics_summary = collector.get_metrics_summary(module_name)

    result = {
        "incident_id": incident_id,
        "module_name": module_name,
        "metrics_summary": metrics_summary
    }
    if isinstance(analysis, dict):
        result.update(analysis)
    
    return result


def process_incident_stream(module_name, stream_data):
    hub = ErrorRecoveryHub()
    if hasattr(hub, 'analyze_and_recover'):
        return hub.analyze_and_recover(module_name, stream_data)
    return {"recovered": False}


def export_incident_analytics(module_name, output_path, format="json"):
    collector = PatchMetricCollector()
    if hasattr(collector, 'export_metrics'):
        return collector.export_metrics(output_path, format)
    return False