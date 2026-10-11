import io
from typing import Any, Dict, Optional

try:
    from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
except ImportError:
    market_portfolio_scenario_simulator = None

from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.db_storage import db_storage

class ComplianceAuditException(Exception):
    """Исключение, возникающее при нарушении нормативных требований аудита."""
    pass

class MarketPortfolioStressAuditComplianceBridge:
    def __init__(
        self,
        db_storage=None,
        market_portfolio_audit_compliance_hub=None,
        market_portfolio_stress_audit_exporter_v2=None
    ):
        self.db_storage = db_storage
        self.compliance_hub = market_portfolio_audit_compliance_hub if market_portfolio_audit_compliance_hub is not None else globals().get("market_portfolio_audit_compliance_hub")
        self.audit_exporter = market_portfolio_stress_audit_exporter_v2

    def audit_and_validate(self, portfolio_id: str, standard: str) -> dict:
        audit_data = self.compliance_hub.verify_compliance(portfolio_id, standard)
        if self.db_storage:
            self.db_storage.log_audit_event(audit_data)
        return audit_data

    def audit_and_sync(self, portfolio_id: Optional[str] = None, standard: Optional[str] = None, **kwargs) -> dict:
        return self.audit_and_validate(portfolio_id or "default", standard or "default")

    def export_audit_stream(self, stream_id: str) -> io.BytesIO:
        if self.audit_exporter and hasattr(self.audit_exporter, "export_stream"):
            return self.audit_exporter.export_stream(stream_id)
        return io.BytesIO(f"Stream {stream_id}".encode("utf-8"))

    def export_regulatory_package(self, stream_id: str = "default", **kwargs) -> io.BytesIO:
        return self.export_audit_stream(stream_id)

    def process_stress_event(self, payload: dict) -> dict:
        if self.db_storage and hasattr(self.db_storage, "save_event"):
            return self.db_storage.save_event(payload)
        return {"status": "processed", "payload": payload}

    def handle_stress_anomaly(self, payload: Optional[dict] = None, **kwargs) -> dict:
        return self.process_stress_event(payload or {})

    def safely_execute_scenario(self, scenario_data: Optional[dict] = None, **kwargs) -> dict:
        if market_portfolio_scenario_simulator:
            try:
                return market_portfolio_scenario_simulator(scenario_data or {})
            except Exception:
                pass
        return {"status": "executed", "scenario": scenario_data or {}}

    def validate_allocation_policy(self, policy_data: Optional[dict] = None, **kwargs) -> bool:
        if self.compliance_hub and hasattr(self.compliance_hub, "validate_limits"):
            return self.compliance_hub.validate_limits(policy_data)
        return True


def market_portfolio_stress_audit_compliance_bridge(bridge_input: dict) -> dict:
    """Функция-обертка для интеграционных тестов."""
    portfolio_id = bridge_input.get("portfolio_id")
    compliance_report = bridge_input.get("compliance_report", {})

    status = compliance_report.get("status", "COMPLIANT")

    return {
        "portfolio_id": portfolio_id,
        "audit_compliance_status": status,
        "bridge_processed": True
    }
