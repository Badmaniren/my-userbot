import io
import os
import random
import string
import uuid
from enum import Enum

try:
    import requests
except ImportError:
    requests = None


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
        self.subsystems = subsystems if subsystems is not None else []

    def _probe_subsystem(self, subsystem_name):
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
        if requests is None:
            return {
                "is_active": False,
                "bytes_read": 0
            }
        try:
            response = requests.get(subsystem_target)
            content = getattr(response, "content", b"")
            return {
                "is_active": True,
                "bytes_read": len(content)
            }
        except Exception:
            return {
                "is_active": False,
                "bytes_read": 0
            }

    def check_audit_integrity(self, audit_id=None):
        full_audit = self.run_full_audit()
        global_status = full_audit.get("global_status", SubsystemHealthStatus.HEALTHY)
        status_str = global_status.value if isinstance(global_status, SubsystemHealthStatus) else str(global_status)
        return {
            "audit_id": audit_id or str(uuid.uuid4()),
            "status": status_str,
            "integrity_ok": global_status != SubsystemHealthStatus.UNHEALTHY,
            "details": full_audit.get("subsystems_details", {})
        }

    def generate_aggregate_health_report(self):
        full_audit = self.run_full_audit()
        global_status = full_audit.get("global_status", SubsystemHealthStatus.HEALTHY)
        status_str = global_status.value if isinstance(global_status, SubsystemHealthStatus) else str(global_status)
        return {
            "report_id": str(uuid.uuid4()),
            "global_status": status_str,
            "subsystems": full_audit.get("subsystems_details", {})
        }

    def evaluate_subsystems(self, subsystems=None):
        if subsystems is not None:
            temp_monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)
            return temp_monitor.run_full_audit()
        return self.run_full_audit()

    def __call__(self, *args, **kwargs):
        payload = args[0] if args and isinstance(args[0], dict) else kwargs
        audit_id = payload.get("audit_id") if isinstance(payload, dict) else None
        return self.check_audit_integrity(audit_id=audit_id)


market_portfolio_stress_audit_health_monitor = MarketPortfolioStressAuditHealthMonitor()
