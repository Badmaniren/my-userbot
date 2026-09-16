import uuid
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()

    def create_ticket(self, incident_data):
        if isinstance(incident_data, dict):
            inc_id = incident_data.get("incident_id") or incident_data.get("id") or uuid.uuid4().hex
        else:
            inc_id = str(incident_data)
        return f"ticket_{inc_id}"

    def process_and_aggregate(self, module_name, exception=None, traceback_str="", incident_id=None):
        if not incident_id:
            if isinstance(module_name, dict):
                incident_id = module_name.get("incident_id") or uuid.uuid4().hex
                module_name = module_name.get("source") or "unknown_module"
            else:
                incident_id = self.hub.capture_failure(module_name, exception, traceback_str)

        analysis = self.hub.analyze_failure(incident_id) if hasattr(self.hub, 'analyze_failure') else {}
        
        metric_payload = self.collector.record_metric({
            "incident_id": incident_id,
            "module_name": str(module_name),
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


def aggregate_incidents(module_name, exception=None, traceback_str=""):
    hub = ErrorRecoveryHub()
    collector = PatchMetricCollector()

    incident_id = hub.capture_failure(module_name, exception, traceback_str)
    analysis = hub.analyze_failure(incident_id)
    
    metric_payload = collector.record_metric({
        "incident_id": incident_id,
        "module_name": str(module_name),
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


def incident_aggregator(data_or_module, *args, **kwargs):
    if isinstance(data_or_module, dict):
        inc = dict(data_or_module)
        if "incident_id" not in inc:
            inc["incident_id"] = inc.get("id") or uuid.uuid4().hex
        return inc
    agg = IncidentAggregator()
    return agg.process_and_aggregate(data_or_module, *args, **kwargs)


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
