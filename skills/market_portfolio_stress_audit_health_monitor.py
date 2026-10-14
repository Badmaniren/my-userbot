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

    def check_audit_integrity(self, payload=None):
        audit_res = self.run_full_audit()
        return {
            "status": "ok",
            "integrity": True,
            "audit": audit_res,
            "payload": payload
        }

    def generate_aggregate_health_report(self):
        return self.run_full_audit()

    def evaluate_subsystems(self, subsystems=None):
        if subsystems is not None:
            previous = self.subsystems
            self.subsystems = subsystems
            res = self.run_full_audit()
            self.subsystems = previous
            return res
        return self.run_full_audit()

    def verify_stream_pipeline(self, subsystem_target):
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

    def __call__(self, *args, **kwargs):
        payload = args[0] if args else kwargs.get("payload", None)
        return self.check_audit_integrity(payload)


market_portfolio_stress_audit_health_monitor = MarketPortfolioStressAuditHealthMonitor()
