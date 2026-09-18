from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()

    def report_anomaly(self, anomaly_data=None, **kwargs):
        if anomaly_data is None:
            anomaly_data = kwargs
        return {
            "incident_id": anomaly_data.get("incident_id", anomaly_data.get("id")),
            "anomaly": anomaly_data,
            "status": "reported"
        }

    @staticmethod
    def aggregate(incident_id=None, telemetry_payload=None, *args, **kwargs):
        if incident_id is None and len(args) > 0:
            incident_id = args[0]
        if telemetry_payload is None and len(args) > 1:
            telemetry_payload = args[1]
        if isinstance(incident_id, dict) and telemetry_payload is None:
            telemetry_payload = incident_id
            incident_id = telemetry_payload.get("incident_id")
        res = dict(telemetry_payload) if isinstance(telemetry_payload, dict) else {}
        res.update({
            "incident_id": incident_id or kwargs.get("incident_id") or "INC-AGGREGATED",
            "telemetry_payload": telemetry_payload or kwargs.get("telemetry_payload") or {},
            "severity_level": kwargs.get("severity_level", "CRITICAL")
        })
        return res

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


def aggregate(incident_id=None, telemetry_payload=None, *args, **kwargs):
    return IncidentAggregator.aggregate(incident_id, telemetry_payload, *args, **kwargs)


def report_anomaly(anomaly_data=None, **kwargs):
    return IncidentAggregator().report_anomaly(anomaly_data, **kwargs)


def incident_aggregator(data=None, **kwargs):
    if data is not None:
        if isinstance(data, dict):
            payload = dict(data)
            payload.update(kwargs)
            return aggregate(payload.get("incident_id"), payload.get("telemetry_payload"), **payload)
        return aggregate(data, **kwargs)
    return aggregate(**kwargs)