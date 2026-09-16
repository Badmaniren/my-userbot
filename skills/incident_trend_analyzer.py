from uuid import uuid4
import json
import io

def start_new(success=True, incident_id=None, error=None, raw_result=None, patch_data=None):
    if incident_id is None:
        incident_id = uuid4().hex
        
    return {
        "incident_id": incident_id,
        "success": success,
        "error": error,
        "raw_result": raw_result,
        "patch_data": patch_data
    }

class IncidentTrendAnalyzer:
    def __init__(self):
        pass

    def analyze_trends(self, module_name):
        if isinstance(module_name, dict):
            return self.analyze_trend(module_name)
        return {
            "module_name": module_name,
            "status": "analyzed",
            "trend": "stable",
            "recurrence_score": 0.0
        }

    def analyze_trend(self, aggregated_data=None):
        if aggregated_data is None:
            aggregated_data = {}
        if isinstance(aggregated_data, str):
            aggregated_data = {"id": aggregated_data}
        incident_id = aggregated_data.get("id") or aggregated_data.get("incident_id")
        return {
            "incident_id": incident_id,
            "status": "analyzed",
            "trend": "stable",
            "recurrence_score": aggregated_data.get("recurrence_score", 0.0)
        }

    def analyze(self, trend_data=None):
        if isinstance(trend_data, dict):
            return self.analyze_trend(trend_data)
        return self.analyze_trends(trend_data)

    def determine_escalation_tier(self, failure_history_count):
        if failure_history_count >= 10:
            return "P1"
        elif failure_history_count >= 5:
            return "P2"
        elif failure_history_count >= 2:
            return "P3"
        return "P4"

incident_trend_analyzer = IncidentTrendAnalyzer

class RecoveryDashboardGenerator:
    def __init__(self):
        pass

    def generate_dashboard(self, metrics, incidents, reports, format="json"):
        dashboard_data = {
            "metrics": metrics,
            "incidents": incidents,
            "reports": reports
        }
        if format == "json":
            return json.dumps(dashboard_data)
        return str(dashboard_data)

    def export_dashboard(self, dashboard_data, file_path):
        if isinstance(dashboard_data, dict):
            payload = json.dumps(dashboard_data)
        else:
            payload = str(dashboard_data)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(payload)
        return True

    def parse_stream_data(self, stream_bytes):
        if isinstance(stream_bytes, io.BytesIO):
            content = stream_bytes.read().decode('utf-8')
        elif isinstance(stream_bytes, bytes):
            content = stream_bytes.decode('utf-8')
        else:
            content = str(stream_bytes)
        return json.loads(content)
