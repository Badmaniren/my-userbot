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

from skills import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_stress_audit_summary_vault import (
    MarketPortfolioStressAuditSummaryVault,
    StorageUnreachableError
)


class SubsystemHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class HealthMonitorExecutionError(Exception):
    pass


class MarketPortfolioStressAuditHealthMonitor:

    def __init__(self, subsystems=None):
        self.subsystems = subsystems if subsystems is not None else []
        self.vault = MarketPortfolioStressAuditSummaryVault()

    def _probe_subsystem(self, subsystem_name):
        try:
            if hasattr(market_portfolio_stress_audit_summary_vault, "fetch_summary"):
                summary = market_portfolio_stress_audit_summary_vault.fetch_summary(subsystem_name)
            else:
                summary = self.vault.fetch_summary(subsystem_name)

            if isinstance(summary, dict):
                status_val = summary.get("status")
                if status_val:
                    try:
                        status = SubsystemHealthStatus(status_val)
                    except ValueError:
                        status = SubsystemHealthStatus.HEALTHY
                else:
                    status = SubsystemHealthStatus.HEALTHY

                return {
                    "subsystem": subsystem_name,
                    "status": status,
                    "token": summary.get("token"),
                    "error": summary.get("error")
                }
        except StorageUnreachableError:
            raise
        except HealthMonitorExecutionError:
            raise
        except Exception as e:
            raise HealthMonitorExecutionError(str(e)) from e

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
            except HealthMonitorExecutionError:
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

    def evaluate_subsystems(self):
        return self.run_full_audit()

    def generate_aggregate_health_report(self):
        return self.run_full_audit()

    def check_audit_integrity(self):
        return self.run_full_audit()

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


market_portfolio_stress_audit_health_monitor = MarketPortfolioStressAuditHealthMonitor


def check_audit_integrity():
    return MarketPortfolioStressAuditHealthMonitor().run_full_audit()


def generate_aggregate_health_report():
    return MarketPortfolioStressAuditHealthMonitor().run_full_audit()


def evaluate_subsystems():
    return MarketPortfolioStressAuditHealthMonitor().run_full_audit()


def run_full_audit():
    return MarketPortfolioStressAuditHealthMonitor().run_full_audit()
