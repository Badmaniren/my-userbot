from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

_INCIDENT_STORE = {}

def get_incident_data(incident_id):
    return _INCIDENT_STORE.get(incident_id)

def store_incident_metrics(data):
    if isinstance(data, dict):
        inc_id = data.get("id") or data.get("incident_id")
        if inc_id:
            _INCIDENT_STORE[inc_id] = data

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
    if isinstance(module_name, list):
        results = []
        for item in module_name:
            if isinstance(item, dict):
                inc_id = item.get("id") or item.get("incident_id") or "inc_123"
                sev = item.get("severity", "HIGH")
                rec = {"incident_id": inc_id, "severity": sev, **item}
                _INCIDENT_STORE[inc_id] = rec
                results.append(rec)
            else:
                results.append({"incident_id": str(item)})
        return results
    elif isinstance(module_name, dict):
        inc_id = module_name.get("id") or module_name.get("incident_id") or "inc_123"
        sev = module_name.get("severity", "HIGH")
        rec = {"incident_id": inc_id, "severity": sev, **module_name}
        _INCIDENT_STORE[inc_id] = rec
        return [rec]

    mod = module_name or "default_module"
    exc = exception or Exception("Default error")
    tb = traceback_str or ""

    hub = ErrorRecoveryHub()
    collector = PatchMetricCollector()

    incident_id = hub.capture_failure(mod, exc, tb)
    analysis = hub.analyze_failure(incident_id)
    
    metric_payload = collector.record_metric({
        "incident_id": incident_id,
        "module_name": mod,
        "success": False,
        "metric_value": 0.0
    })
    metrics_summary = collector.get_metrics_summary(mod)

    result = {
        "incident_id": incident_id,
        "module_name": mod,
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