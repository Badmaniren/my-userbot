import requests
import uuid
import os
try:
    from skills.db_storage import db_storage
except (ImportError, AttributeError):
    db_storage = None

try:
    from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
except (ImportError, AttributeError):
    market_portfolio_stress_audit_summary_vault = None

try:
    from skills.market_portfolio_data_exporter import market_portfolio_data_exporter
except (ImportError, AttributeError):
    market_portfolio_data_exporter = None


def start_new(dependencies, telemetry_stream=None):
    collector = dependencies.get("market_portfolio_collector_agent")
    exporter = dependencies.get("market_portfolio_stress_audit_exporter_v2")

    try:
        collected_data = collector.collect(telemetry_stream) if collector else {}
    except Exception as e:
        if requests:
            response = requests.post("http://localhost/error", json={"error": str(e)})
            response.raise_for_status()
        raise e

    if exporter:
        export_result = None
        if hasattr(exporter, "export") and callable(exporter.export):
            export_result = exporter.export(collected_data)
        elif hasattr(exporter, "export_report") and callable(exporter.export_report):
            export_result = exporter.export_report(collected_data)
        elif callable(exporter):
            export_result = exporter(collected_data)

        if isinstance(export_result, dict):
            collected_data.update(export_result)

    if collected_data:
        if "telemetry_id" not in collected_data:
            collected_data["telemetry_id"] = uuid.uuid4().hex
        requests.post("http://localhost/telemetry", json=collected_data)

    return collected_data


class MarketPortfolioStressAuditRiskTelemetryClass:
    def process_telemetry(self, telemetry_input):
        portfolio_id = telemetry_input.get("portfolio_id")
        audit_id = telemetry_input.get("audit_id")

        telemetry_id = uuid.uuid4().hex
        return {
            "portfolio_id": portfolio_id,
            "audit_id": audit_id,
            "telemetry_id": telemetry_id,
            "status": "processed"
        }


market_portfolio_stress_audit_risk_telemetry = MarketPortfolioStressAuditRiskTelemetryClass()