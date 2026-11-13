from datetime import datetime
import uuid
import json
import requests

def uuid4():
    return str(uuid.uuid4())

class RepoHealthIncidentTracker:
    def __init__(self):
        self._incidents = {}

    def track_incident(self, repo_id, incident_type, severity, description, metadata=None):
        incident_id = uuid4()
        incident = {
            "id": incident_id,
            "repo_id": repo_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "metadata": metadata if metadata is not None else {},
            "status": "OPEN",
            "resolver": None,
            "resolution_notes": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._incidents[incident_id] = incident
        return incident_id

    def get_incident(self, incident_id):
        return self._incidents.get(incident_id)

    def list_incidents_by_repo(self, repo_id):
        return [inc for inc in self._incidents.values() if inc["repo_id"] == repo_id]

    def resolve_incident(self, incident_id, resolver, resolution_notes):
        if incident_id not in self._incidents:
            return False
        self._incidents[incident_id].update({
            "status": "RESOLVED",
            "resolver": resolver,
            "resolution_notes": resolution_notes
        })
        return True

    def get_incident_metrics(self, repo_id):
        incidents = self.list_incidents_by_repo(repo_id)
        breakdown = {}
        for inc in incidents:
            sev = inc["severity"]
            breakdown[sev] = breakdown.get(sev, 0) + 1
        return {"total": len(incidents), "breakdown": breakdown}

    def ingest_anomaly_stream(self, stream):
        try:
            data = stream.read()
            if not data:
                return False
            payload = json.loads(data)
            required = ["repo_id", "anomaly_code", "level", "details"]
            if not all(k in payload for k in required):
                return False
            self.track_incident(
                payload["repo_id"],
                payload["anomaly_code"],
                payload["level"],
                payload["details"]
            )
            return True
        except (json.JSONDecodeError, AttributeError, Exception):
            return False

    def export_incident(self, incident_id, endpoint):
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        try:
            response = requests.post(endpoint, json=incident)
            return response.status_code == 200
        except requests.RequestException:
            return False

_default_tracker = RepoHealthIncidentTracker()

def track_incident(repo_id, incident_type, severity, description, metadata=None):
    return _default_tracker.track_incident(
        repo_id, incident_type, severity, description, metadata
    )