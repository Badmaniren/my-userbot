from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from skills.db_storage import DBStorage


class SubsystemHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class HealthMonitorExecutionError(Exception):
    pass


class StorageUnreachableError(Exception):
    pass


class MarketPortfolioStressAuditHealthMonitor:

    def __init__(self, subsystems: Optional[List[str]] = None) -> None:
        if subsystems is not None and not isinstance(subsystems, list):
            raise TypeError("subsystems must be a list of strings")
        self.subsystems: List[str] = list(subsystems) if subsystems is not None else []
        self.db: DBStorage = DBStorage()

    def _probe_subsystem(self, subsystem_name: str) -> Dict[str, Any]:
        if not isinstance(subsystem_name, str):
            raise TypeError("subsystem_name must be a string")
        return {
            "subsystem": subsystem_name,
            "status": SubsystemHealthStatus.HEALTHY,
            "token": None,
            "error": None
        }

    def run_full_audit(self) -> Dict[str, Any]:
        subsystems_details: Dict[str, Dict[str, Any]] = {}
        global_status = SubsystemHealthStatus.HEALTHY

        for sub in self.subsystems:
            try:
                result = self._probe_subsystem(sub)
            except StorageUnreachableError:
                raise
            except Exception as e:
                raise HealthMonitorExecutionError(str(e)) from e

            subsystems_details[sub] = result
            status = result.get("status")
            if status == SubsystemHealthStatus.DEGRADED and global_status == SubsystemHealthStatus.HEALTHY:
                global_status = SubsystemHealthStatus.DEGRADED
            elif status == SubsystemHealthStatus.UNHEALTHY:
                global_status = SubsystemHealthStatus.UNHEALTHY

        return {
            "global_status": global_status,
            "subsystems_details": subsystems_details
        }

    def verify_stream_pipeline(self, subsystem_target: str) -> Dict[str, Any]:
        if not isinstance(subsystem_target, str):
            raise TypeError("subsystem_target must be a string")
        if requests is None:
            return {
                "is_active": False,
                "bytes_read": 0
            }
        try:
            response = requests.get(subsystem_target)
            content = response.content
            return {
                "is_active": True,
                "bytes_read": len(content)
            }
        except Exception:
            return {
                "is_active": False,
                "bytes_read": 0
            }
