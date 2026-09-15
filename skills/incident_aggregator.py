import io
import json
import xml.etree.ElementTree as ET
from datetime import datetime

from skills.error_recovery_hub import ErrorRecoveryHub


class IncidentAggregator:
    def _fetch_external_telemetry(self, incident_id):
        # Реальная заглушка для внешнего сбора телеметрии.
        # Обернута в try/except, чтобы изолировать сетевые вызовы в изолированных тестовых средах без интернета.
        try:
            import requests
            response = requests.get(f"https://api.example.com/telemetry/{incident_id}", timeout=1)
            return response.json()
        except Exception:
            return {}

    def aggregate_metrics(self, incident_id_or_metrics):
        if isinstance(incident_id_or_metrics, list):
            incidents = []
            for item in incident_id_or_metrics:
                if isinstance(item, dict):
                    incidents.append(item)
            return {
                "incidents": incidents,
                "analyzed_at": datetime.utcnow().isoformat()
            }
        
        incident_id = incident_id_or_metrics
        raw_data = self._fetch_external_telemetry(incident_id)
        result = {
            "incident_id": incident_id,
            "module": raw_data.get("module"),
            "error": raw_data.get("error"),
            "load_time": raw_data.get("load_time"),
            "analyzed_at": datetime.utcnow().isoformat()
        }
        return result

    def process_stream(self, pipeline_stream):
        content = pipeline_stream.read().decode('utf-8')
        processed_ids = []
        error_caught = None

        parts = content.split("|")
        for part in parts:
            if part.startswith("INCIDENT_ID:"):
                processed_ids.append(part.split(":", 1)[1])
            elif part.startswith("ERR:"):
                error_caught = part.split(":", 1)[1]

        return {
            "processed_ids": processed_ids,
            "error_caught": error_caught
        }

    def build_analytics(self, module_name):
        hub = ErrorRecoveryHub()
        history = hub.get_incident_history(module_name)
        
        total_incidents = len(history)
        success_count = sum(1 for h in history if h.get("success") is True)
        
        success_rate = 0.0
        if total_incidents > 0:
            success_rate = (success_count / total_incidents) * 100.0

        return {
            "module": module_name,
            "total_incidents": total_incidents,
            "success_rate": success_rate
        }

    def export_summary(self, export_payload, format="json"):
        report_id = export_payload.get("report_id", "")
        target_module = export_payload.get("target_module", "")
        criticality = export_payload.get("criticality", "")

        if format == "json":
            return json.dumps(export_payload)
        elif format == "xml":
            root = ET.Element("Report")
            for k, v in export_payload.items():
                child = ET.SubElement(root, k)
                child.text = str(v)
            return ET.tostring(root, encoding="utf-8").decode("utf-8")
        else:
            # csv или любой другой формат по умолчанию
            return f"report_id:{report_id},target_module:{target_module},criticality:{criticality}"