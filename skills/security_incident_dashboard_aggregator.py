import json
import requests
from skills.vulnerability_scanner import vulnerability_scanner
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_aggregator import incident_aggregator


class SecurityIncidentDashboardAggregator:
    def aggregate_system_metrics(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": "Request failed", "status_code": response.status_code}
        
        if hasattr(response, 'json') and callable(response.json):
            try:
                data = response.json()
                if isinstance(data, dict):
                    return data
            except (ValueError, TypeError, json.JSONDecodeError):
                pass
        
        if hasattr(response, 'content'):
            return json.loads(response.content.decode('utf-8'))
        
        return {}

    def generate_consolidated_dashboard(self, file_path):
        metrics_count = 0
        raw_stream_read = False
        with open(file_path, 'rb') as f:
            content = f.read()
            if content:
                raw_stream_read = True
                metrics_count = len(content.split(b'\n'))

        return {
            "metrics_count": metrics_count,
            "raw_stream_read": raw_stream_read
        }

    def compute_severity_distribution(self, incidents_list):
        distribution = {}
        for inc in incidents_list:
            sev = inc.get("severity", "UNKNOWN")
            distribution[sev] = distribution.get(sev, 0) + 1
        return distribution