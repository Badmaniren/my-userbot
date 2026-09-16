from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()

    def process_and_aggregate(self, module_name, exception=None, traceback_str=None, incident_id=None):
        if not incident_id:
            incident_id = self.hub.capture_failure(module_name, exception, traceback_str)

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


def aggregate_incidents(module_name=None, exception=None, traceback_str=None, **kwargs):
    if isinstance(module_name, dict):
        event = module_name
        inc_id = event.get("id") or event.get("incident_id") or "inc_aggregated"
        mod_name = event.get("source") or event.get("module_name") or "raw_event"
        metrics = event.get("metrics", {})
        return {
            "incident_id": inc_id,
            "module_name": mod_name,
            "metrics": metrics,
            "data": event,
            "count": metrics.get("count", 1),
            "status": "aggregated"
        }

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
