import uuid
import json
import datetime
import requests

class RepoHealthIncidentTracker:
    def __init__(self):
        self.incidents = {}

    def track_incident(self, repo_id, incident_type, severity, description, metadata=None):
        incident_id = uuid.uuid4().hex
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
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.incidents[incident_id] = incident
        return incident_id

    def get_incident(self, incident_id):
        return self.incidents.get(incident_id, None)

    def ingest_anomaly_stream(self, stream_data):
        try:
            content = stream_data.read()
            if not content:
                return False
            payload = json.loads(content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return False

        repo_id = payload.get("repo_id")
        incident_type = payload.get("anomaly_code")
        severity = payload.get("level")
        description = payload.get("details")

        if not all([repo_id, incident_type, severity, description]):
            return False

        self.track_incident(
            repo_id=repo_id,
            incident_type=incident_type,
            severity=severity,
            description=description
        )
        return True

    def list_incidents_by_repo(self, repo_id):
        return [inc for inc in self.incidents.values() if inc["repo_id"] == repo_id]

    def resolve_incident(self, incident_id, resolver_name, resolution_notes):
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        incident["status"] = "RESOLVED"
        incident["resolver"] = resolver_name
        incident["resolution_notes"] = resolution_notes
        return True

    def get_incident_metrics(self, repo_id):
        repo_incidents = self.list_incidents_by_repo(repo_id)
        total = len(repo_incidents)
        breakdown = {}
        for inc in repo_incidents:
            sev = inc["severity"]
            breakdown[sev] = breakdown.get(sev, 0) + 1
        return {
            "total": total,
            "breakdown": breakdown
        }

    def get_metrics(self, repo_id):
        return self.get_incident_metrics(repo_id)

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