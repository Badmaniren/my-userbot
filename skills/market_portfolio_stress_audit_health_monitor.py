from enum import Enum
import requests

from skills.db_storage import save_audit_result, get_audit_result


class SubsystemHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class HealthMonitorExecutionError(Exception):
    pass


class StorageUnreachableError(Exception):
    pass


class MarketPortfolioStressAuditHealthMonitor:

    def __init__(self, subsystems=None):
        if subsystems is not None:
            if not isinstance(subsystems, (list, tuple, set)):
                raise TypeError("subsystems must be a list, tuple, or set of subsystem names")
            for sub in subsystems:
                if not isinstance(sub, str) or not sub.strip():
                    raise ValueError("Each subsystem name must be a non-empty string")
            self.subsystems = list(subsystems)
        else:
            self.subsystems = []

    def _probe_subsystem(self, subsystem_name):
        if not isinstance(subsystem_name, str) or not subsystem_name.strip():
            raise ValueError("subsystem_name must be a non-empty string")
        return {
            "subsystem": subsystem_name,
            "status": SubsystemHealthStatus.HEALTHY,
            "token": None,
            "error": None
        }

    def run_full_audit(self):
        subsystems_details = {}
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

    def verify_stream_pipeline(self, subsystem_target):
        if not isinstance(subsystem_target, str) or not subsystem_target.strip():
            raise ValueError("subsystem_target must be a non-empty string URL")

        response = requests.get(subsystem_target)
        response.raise_for_status()
        content = response.content
        return {
            "is_active": True,
            "bytes_read": len(content)
        }
