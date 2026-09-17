import uuid
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()

    def process_and_aggregate(self, module_name=None, exception=None, traceback_str=None, incident_id=None, **kwargs):
        if isinstance(module_name, (list, dict)):
            items = module_name if isinstance(module_name, list) else [module_name]
            first_item = items[0] if items and isinstance(items[0], dict) else {}
            inc_id = first_item.get("incident_id") or incident_id or f"inc-{uuid.uuid4().hex[:8]}"
            mod_name = first_item.get("module_name") or "default"
            return {
                "incident_id": inc_id,
                "module_name": mod_name,
                "data": first_item,
                "aggregated_count": len(items)
            }

        if not incident_id:
            incident_id = self.hub.capture_failure(module_name, exception, traceback_str)

        analysis = self.hub.analyze_failure(incident_id) if hasattr(self.hub, 'analyze_failure') else {}
        
        metric_payload = self.collector.record_metric({
            "incident_id": incident_id,
            "module_name": module_name,
            "success": False,
            "metric_value": 0.0
        })

        metrics_summary = self.collector.get_metrics_summary(module_name) if hasattr(self.collector, 'get_metrics_summary') else {}
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
    hub = ErrorRecoveryHub()
    collector = PatchMetricCollector()

    if isinstance(module_name, (list, dict)):
        data_list = module_name if isinstance(module_name, list) else [module_name]
        results = []
        first_item = {}
        for item in data_list:
            if isinstance(item, dict):
                if not first_item:
                    first_item = item
                inc_id = item.get("incident_id") or f"inc-{uuid.uuid4().hex[:8]}"
                mod_name = item.get("module_name") or item.get("module") or "default"
                results.append({
                    "incident_id": inc_id,
                    "module_name": mod_name,
                    "status": "AGGREGATED",
                    "data": item
                })
        return {
            "aggregated_count": len(results),
            "incidents": results,
            "data": first_item,
            "incident_id": first_item.get("incident_id") or (results[0]["incident_id"] if results else None)
        }

    if not module_name and kwargs:
        module_name = kwargs.get("module_name", "default")

    incident_id = hub.capture_failure(module_name, exception, traceback_str) if (exception or traceback_str) else kwargs.get("incident_id") or f"inc-{uuid.uuid4().hex[:8]}"
    analysis = hub.analyze_failure(incident_id) if hasattr(hub, 'analyze_failure') else {}
    
    metric_payload = collector.record_metric({
        "incident_id": incident_id,
        "module_name": module_name,
        "success": False,
        "metric_value": 0.0
    })
    metrics_summary = collector.get_metrics_summary(module_name) if hasattr(collector, 'get_metrics_summary') else {}

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
