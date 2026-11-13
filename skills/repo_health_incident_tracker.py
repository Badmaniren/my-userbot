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
        if metadata is None:
            metadata = {}
        incident_id = uuid4()
        incident = {
            "id": incident_id,
            "repo_id": repo_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "metadata": metadata,
            "status": "OPEN",
            "resolver": None,
            "resolution_notes": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._incidents[incident_id] = incident
        return incident_id

    def get_incident(self, incident_id):
        return self._incidents.get(incident_id)

    def ingest_anomaly_stream(self, stream):
        try:
            if isinstance(stream, int):
                return False
            data = stream.read()
            if not data:
                return False
            payload = json.loads(data.decode("utf-8"))
            repo_id = payload.get("repo_id")
            anomaly_code = payload.get("anomaly_code")
            level = payload.get("level")
            details = payload.get("details")
            if not repo_id or not anomaly_code:
                return False
            self.track_incident(
                repo_id=repo_id,
                incident_type=anomaly_code,
                severity=level if level else "UNKNOWN",
                description=details if details else ""
            )
            return True
        except Exception:
            return False

    def list_incidents_by_repo(self, repo_id):
        return [inc for inc in self._incidents.values() if inc["repo_id"] == repo_id]

    def resolve_incident(self, incident_id, resolver, resolution_notes):
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        incident["status"] = "RESOLVED"
        incident["resolver"] = resolver
        incident["resolution_notes"] = resolution_notes
        return True

    def get_incident_metrics(self, repo_id):
        incidents = self.list_incidents_by_repo(repo_id)
        total = len(incidents)
        breakdown = {}
        for inc in incidents:
            sev = inc["severity"]
            breakdown[sev] = breakdown.get(sev, 0) + 1
        return {
            "total": total,
            "breakdown": breakdown
        }

    def export_incident(self, incident_id, endpoint):
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        try:
            response = requests.post(endpoint, json=incident)
            return response.status_code == 200
        except Exception:
            return False

# Глобальный инстанс для поддержки функции track_incident на уровне модуля
_GLOBAL_TRACKER = RepoHealthIncidentTracker()

def track_incident(repo_id, incident_type, severity, description, metadata=None):
    return _GLOBAL_TRACKER.track_incident(
        repo_id=repo_id,
        incident_type=incident_type,
        severity=severity,
        description=description,
        metadata=metadata
    )