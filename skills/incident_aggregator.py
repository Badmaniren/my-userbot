from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

_INCIDENT_STORE = {}

def store_incident_metrics(data):
    if isinstance(data, dict):
        incident_id = data.get("incident_id")
        if incident_id:
            _INCIDENT_STORE[incident_id] = data
            return True
    return False

def get_incident_data(incident_id):
    return _INCIDENT_STORE.get(incident_id)

def aggregate_incident(incident_id, error_message=None):
    data = get_incident_data(incident_id)
    if not data:
        data = {"incident_id": incident_id, "error_message": error_message}
        _INCIDENT_STORE[incident_id] = data
    return data

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()
        self.incidents = _INCIDENT_STORE

    def get_incident_data(self, incident_id):
        return get_incident_data(incident_id)

    def get_downtime_metrics(self, incident_id):
        data = get_incident_data(incident_id)
        if data and "duration" in data:
            return {"duration": data["duration"]}
        if data and "start_timestamp" in data and "end_timestamp" in data:
            return {"duration": data["end_timestamp"] - data["start_timestamp"]}
        return {"duration": 0.0}

    def get_incident(self, incident_id):
        return self.incidents.get(incident_id)

    def get_incident_details(self, incident_id):
        return self.incidents.get(incident_id)

    def update_status(self, incident_id, status, **kwargs):
        if incident_id in self.incidents and isinstance(self.incidents[incident_id], dict):
            self.incidents[incident_id]["status"] = status
            self.incidents[incident_id].update(kwargs)

    def collect(self, incident_id=None, component=None, severity=None, **kwargs):
        if incident_id:
            payload = {"incident_id": incident_id, "component": component, "severity": severity}
            payload.update(kwargs)
            self.incidents[incident_id] = payload
            return payload
        return {}

    def ingest_raw_stream(self, stream_payload):
        return {"status": "processed", "stream": stream_payload}

    def process_and_aggregate(self, module_name, exception, traceback_str, incident_id=None):
        if not incident_id:
            incident_id = self.hub.capture_failure(module_name, exception, traceback_str)

        analysis = self.hub.analyze_failure(incident_id) if hasattr(self.hub, 'analyze_failure') else {}
        
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
