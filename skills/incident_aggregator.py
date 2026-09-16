from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import PatchMetricCollector

import uuid
import time

class IncidentAggregator:
    def __init__(self):
        self.hub = ErrorRecoveryHub()
        self.collector = PatchMetricCollector()
        self.incidents = {}

    def aggregate(self, telemetry=None, incident_tag=None, **kwargs):
        """
        Aggregates raw incident data, telemetry payloads, or positional error info into a unified incident dictionary.
        """
        if isinstance(telemetry, dict):
            payload = dict(telemetry)
            payload.update(kwargs)
            inc_id = payload.get("id") or payload.get("incident_id") or f"inc_{uuid.uuid4().hex[:8]}"
            source = payload.get("source") or payload.get("source_id") or "unknown_source"
            title = payload.get("title", "Aggregated Incident")
            url = payload.get("url", "")
            timestamp = payload.get("timestamp", time.time())
            raw_payload = payload.get("raw_payload", str(payload))

            result = {
                "id": inc_id,
                "incident_id": inc_id,
                "source": source,
                "source_id": source,
                "title": title,
                "url": url,
                "timestamp": timestamp,
                "raw_payload": raw_payload,
                "status": payload.get("status", "aggregated"),
                "details": payload
            }
            if incident_tag:
                result["tag"] = incident_tag
            self.incidents[inc_id] = result
            return result

        # Positional capture fallback (module_name, exception, traceback_str)
        module_name = telemetry or "unknown_module"
        exception = kwargs.get("exception") or incident_tag
        traceback_str = kwargs.get("traceback_str", "")
        incident_id = kwargs.get("incident_id")
        return self.process_and_aggregate(module_name, exception, traceback_str, incident_id)

    def create_ticket(self, incident_data):
        if isinstance(incident_data, dict):
            inc_id = incident_data.get("id") or incident_data.get("incident_id") or uuid.uuid4().hex[:8]
        else:
            inc_id = str(incident_data)
        return f"ticket_{inc_id}"

    def get_incident_details(self, incident_id):
        return self.incidents.get(incident_id, {"incident_id": incident_id, "status": "not_found"})

    def update_status(self, incident_id, status, **kwargs):
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status
            self.incidents[incident_id].update(kwargs)
            return self.incidents[incident_id]
        return {"incident_id": incident_id, "status": status, **kwargs}

    def ingest_raw_stream(self, stream_payload):
        if hasattr(stream_payload, "read"):
            content = stream_payload.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
        else:
            content = str(stream_payload)
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        res = {
            "id": inc_id,
            "incident_id": inc_id,
            "raw_stream": content,
            "status": "ingested"
        }
        self.incidents[inc_id] = res
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