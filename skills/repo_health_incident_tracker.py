from datetime import datetime
import uuid
import json
import requests

def uuid4():
    return uuid.uuid4()

class RepoHealthIncidentTracker:
    def __init__(self):
        self._incidents = {}

    def track_incident(self, repo_id, incident_type, severity, description, metadata=None):
        incident_id_uuid = uuid4()
        incident_id = str(incident_id_uuid)
        incident = {
            "id": incident_id,
            "repo_id": repo_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "metadata": metadata or {},
            "status": "OPEN",
            "resolver": None,
            "resolution_notes": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._incidents[incident_id] = incident
        return incident_id

    def get_incident(self, incident_id):
        return self._incidents.get(incident_id)

    def ingest_anomaly_stream(self, file_stream):
        content = file_stream.read()
        if not content:
            return False
        try:
            data = json.loads(content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        
        repo_id = data.get("repo_id")
        anomaly_code = data.get("anomaly_code")
        level = data.get("level")
        details = data.get("details")

        if not all([repo_id, anomaly_code, level]):
            return False

        self.track_incident(
            repo_id=repo_id,
            incident_type=anomaly_code,
            severity=level,
            description=details or ""
        )
        return True

    def list_incidents_by_repo(self, repo_id):
        return [inc for inc in self._incidents.values() if inc["repo_id"] == repo_id]

    def resolve_incident(self, incident_id, resolver, resolution_notes):
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
        incident["status"] = "RESOLVED"
        incident["resolver"] = resolver
        incident["resolution_notes"] = resolution_notes
        return True

    def get_incident_metrics(self, repo_id):
        incidents = self.list_incidents_by_repo(repo_id)
        breakdown = {}
        for inc in incidents:
            sev = inc["severity"]
            breakdown[sev] = breakdown.get(sev, 0) + 1
        return {
            "total": len(incidents),
            "breakdown": breakdown
        }

    def export_incident(self, incident_id, endpoint):
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        try:
            response = requests.post(endpoint, json=incident)
            return response.status_code == 200
        except requests.RequestException:
            return False

_global_tracker = RepoHealthIncidentTracker()

def track_incident(repo_id, incident_type, severity, description, metadata=None):
    return _global_tracker.track_incident(
        repo_id=repo_id,
        incident_type=incident_type,
        severity=severity,
        description=description,
        metadata=metadata
    )