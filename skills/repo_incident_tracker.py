from datetime import datetime
from enum import Enum
import json
import os
from typing import Any, Dict, List, Optional
import uuid


class IncidentStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentTracker:
    """
    Хранение и управление жизненным циклом инцидентов репозитория,
    возникающих при обнаружении аномалий, сбоев и уязвимостей.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        repo_path: Optional[str] = None,
        logger: Optional[Any] = None,
    ):
        if storage_path:
            self.storage_path = storage_path
        elif repo_path:
            self.storage_path = os.path.join(repo_path, "incidents.json")
        else:
            self.storage_path = "incidents.json"

        self.repo_path = repo_path
        self.logger = logger
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path and os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.incidents = data.get("incidents", {})
            except (json.JSONDecodeError, OSError) as e:
                if self.logger and hasattr(self.logger, "log_error"):
                    self.logger.log_error("storage_read_error", str(e))
                self.incidents = {}

    def _save(self) -> None:
        if not self.storage_path:
            return
        dir_name = os.path.dirname(self.storage_path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except OSError as e:
                if self.logger and hasattr(self.logger, "log_error"):
                    self.logger.log_error("storage_mkdir_error", str(e))
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"incidents": self.incidents}, f, indent=2)
        except OSError as e:
            if self.logger and hasattr(self.logger, "log_error"):
                self.logger.log_error("storage_write_error", str(e))
            raise

    def create_incident(
        self,
        title: str,
        description: str,
        severity: Any,
        **kwargs: Any,
    ) -> str:
        incident_id = str(uuid.uuid4())
        sev_value = severity.value if isinstance(severity, IncidentSeverity) else str(severity)

        incident: Dict[str, Any] = {
            "id": incident_id,
            "title": title,
            "description": description,
            "severity": sev_value,
            "status": IncidentStatus.OPEN.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        for k, v in kwargs.items():
            if k not in incident:
                incident[k] = v

        self.incidents[incident_id] = incident
        self._save()

        if self.logger and hasattr(self.logger, "log_event"):
            self.logger.log_event("incident_created", f"Created incident {incident_id}: {title}")

        return incident_id

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self.incidents.get(incident_id)

    def update_status(self, incident_id: str, new_status: Any) -> Dict[str, Any]:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident with ID {incident_id} not found")

        status_value = new_status.value if isinstance(new_status, IncidentStatus) else str(new_status)
        self.incidents[incident_id]["status"] = status_value
        self.incidents[incident_id]["updated_at"] = datetime.now().isoformat()
        self._save()

        if self.logger and hasattr(self.logger, "log_event"):
            self.logger.log_event(
                "incident_status_updated",
                f"Incident {incident_id} updated to {status_value}",
            )

        return self.incidents[incident_id]

    def list_incidents(
        self,
        status: Optional[Any] = None,
        severity: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        results = list(self.incidents.values())
        if status is not None:
            status_value = status.value if isinstance(status, IncidentStatus) else str(status)
            results = [inc for inc in results if inc.get("status") == status_value]
        if severity is not None:
            sev_value = severity.value if isinstance(severity, IncidentSeverity) else str(severity)
            results = [inc for inc in results if inc.get("severity") == sev_value]
        return results

    def record_anomaly_incident(
        self,
        anomaly: Dict[str, Any],
        severity: Any = IncidentSeverity.HIGH,
    ) -> str:
        metric = anomaly.get("metric", "unknown_metric")
        deviation = anomaly.get("deviation", "anomaly")
        val = anomaly.get("value", "N/A")
        title = f"Anomaly in metric: {metric}"
        description = f"Detected anomaly deviation '{deviation}' with value {val}"
        return self.create_incident(
            title=title,
            description=description,
            severity=severity,
            anomaly_payload=anomaly,
        )

    def record_vulnerability_incident(
        self,
        vulnerability: Dict[str, Any],
        severity: Any = IncidentSeverity.CRITICAL,
    ) -> str:
        name = vulnerability.get("name") or "unknown_component"
        cve = vulnerability.get("cve")
        desc = vulnerability.get("description") or f"Vulnerability detected in component {name}"
        if cve:
            title = f"Vulnerability {cve}: {name}"
        else:
            title = f"Vulnerability: {name}"
        return self.create_incident(
            title=title,
            description=desc,
            severity=severity,
            vulnerability_payload=vulnerability,
        )

    def resolve_incident(self, incident_id: str) -> Dict[str, Any]:
        return self.update_status(incident_id, IncidentStatus.RESOLVED)

    def close_incident(self, incident_id: str) -> Dict[str, Any]:
        return self.update_status(incident_id, IncidentStatus.CLOSED)
