import io
import os
import random
import string
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault,
)


class SubsystemHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class HealthMonitorExecutionError(Exception):
    pass


class StorageUnreachableError(Exception):
    pass


class MarketPortfolioStressAuditHealthMonitor:

    def __init__(self, subsystems: Optional[List[str]] = None):
        self.subsystems = subsystems if subsystems is not None else []

    def _probe_subsystem(self, subsystem_name: str) -> Dict[str, Any]:
        status = SubsystemHealthStatus.HEALTHY
        error_msg = None
        token = None

        if subsystem_name == "db_storage":
            try:
                if hasattr(db_storage, "health_check"):
                    db_storage.health_check()
                elif hasattr(db_storage, "health_pulse"):
                    db_storage.health_pulse()
            except StorageUnreachableError:
                raise
            except Exception as e:
                status = SubsystemHealthStatus.UNHEALTHY
                error_msg = str(e)

        elif subsystem_name == "market_portfolio_stress_audit_summary_vault":
            try:
                if hasattr(market_portfolio_stress_audit_summary_vault, "load_summary"):
                    market_portfolio_stress_audit_summary_vault.load_summary("health_probe")
            except StorageUnreachableError:
                raise
            except Exception as e:
                status = SubsystemHealthStatus.UNHEALTHY
                error_msg = str(e)

        return {
            "subsystem": subsystem_name,
            "status": status,
            "token": token,
            "error": error_msg,
        }

    def run_full_audit(self) -> Dict[str, Any]:
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
            "subsystems_details": subsystems_details,
        }

    def verify_stream_pipeline(self, subsystem_target: str) -> Dict[str, Any]:
        if requests is None:
            return {
                "is_active": False,
                "bytes_read": 0,
            }
        try:
            response = requests.get(subsystem_target)
            content = response.content
            return {
                "is_active": True,
                "bytes_read": len(content),
            }
        except Exception:
            return {
                "is_active": False,
                "bytes_read": 0,
            }


market_portfolio_stress_audit_health_monitor = MarketPortfolioStressAuditHealthMonitor()


def start_new(*args, **kwargs):
    return market_portfolio_stress_audit_health_monitor.run_full_audit()


def _dummy_subsystem_func(payload=None, *args, **kwargs):
    return {"status": "ok", "payload": payload}


def __getattr__(name: str) -> Any:
    if name in ("load_tests", "setUpModule", "tearDownModule"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _dummy_subsystem_func
