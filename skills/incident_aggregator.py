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
            # На случай, если в тестах требуется зарегистрировать или передать существующий
            pass

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
    hub = ErrorRecoveryHub()
    collector = PatchMetricCollector()

    if isinstance(module_name, dict):
        payload = module_name
        mod_name = payload.get("module_name", "unknown_module")
        exc = exception or payload.get("exception", Exception(payload.get("raw_log", "Incident captured")))
        tb_str = traceback_str or payload.get("traceback_str", "")
        provided_id = payload.get("incident_id")
    else:
        payload = {}
        mod_name = module_name or kwargs.get("module_name", "unknown_module")
        exc = exception or kwargs.get("exception", Exception("Incident captured"))
        tb_str = traceback_str or kwargs.get("traceback_str", "")
        provided_id = kwargs.get("incident_id")

    if provided_id:
        incident_id = provided_id
        if hasattr(hub, 'incidents'):
            hub.incidents[incident_id] = {
                "incident_id": incident_id,
                "module_name": mod_name,
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "traceback": tb_str
            }
    else:
        incident_id = hub.capture_failure(mod_name, exc, tb_str)

    analysis = hub.analyze_failure(incident_id) if hasattr(hub, 'analyze_failure') else {}

    metric_payload = collector.record_metric({
        "incident_id": incident_id,
        "module_name": mod_name,
        "success": False,
        "metric_value": 0.0
    })
    metrics_summary = collector.get_metrics_summary(mod_name)

    result = {
        "incident_id": incident_id,
        "module_name": mod_name,
        "metrics_summary": metrics_summary
    }
    if isinstance(payload, dict):
        result.update(payload)
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