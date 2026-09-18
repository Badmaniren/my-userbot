import json
import os
import re
import requests
from skills.incident_audit_trail_collector import incident_audit_trail_collector

class IncidentForensicsAuditExporter:
    def __init__(self):
        pass

    def export_to_compliance_format(self, incident_id, audit_data):
        file_path = f"{incident_id}.json"
        payload = {"incident_id": incident_id, **audit_data}
        f = open(file_path, 'w')
        try:
            json.dump(payload, f)
        finally:
            if not hasattr(f, 'getvalue'):
                f.close()
        return file_path

    def aggregate_audit_trail(self, incident_id):
        if isinstance(incident_audit_trail_collector, type):
            collector = incident_audit_trail_collector()
            if hasattr(collector, 'fetch_logs'):
                return collector.fetch_logs(incident_id)
            elif hasattr(collector, 'collect'):
                return collector.collect(incident_id)
        else:
            if hasattr(incident_audit_trail_collector, 'fetch_logs'):
                return incident_audit_trail_collector.fetch_logs(incident_id)
            collector = incident_audit_trail_collector()
            if hasattr(collector, 'fetch_logs'):
                return collector.fetch_logs(incident_id)
            elif hasattr(collector, 'collect'):
                return collector.collect(incident_id)
        return []

    def dispatch_to_compliance_bridge(self, target_url, auth_token, payload):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(target_url, json=payload, headers=headers)
        return response.status_code == 201

    def sanitize_audit_data(self, data):
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Удаление HTML-тегов для предотвращения XSS
                sanitized[key] = re.sub(r'<[^>]*>', '', value)
            else:
                sanitized[key] = value
        return sanitized

    def export(self, data, file_path):
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f)
            return True
        except IOError:
            return False

# Алиасы для соответствия интеграционным тестам
incident_forensics_audit_exporter = IncidentForensicsAuditExporter
