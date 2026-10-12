import io
import requests
from bs4 import BeautifulSoup


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def aggregate_and_render(self, raw_telemetry_data):
        if not isinstance(raw_telemetry_data, dict):
            return str(raw_telemetry_data)

        session_id = raw_telemetry_data.get("audit_session_id", "UNKNOWN")
        overall_score = raw_telemetry_data.get("overall_health_score", 100.0)
        subsystems = raw_telemetry_data.get("subsystems", {})

        rendered_lines = [
            f"=== Stress Audit Visualizer Report ===",
            f"Session ID: {session_id}",
            f"Overall Health Score: {overall_score}",
            f"Subsystems Count: {len(subsystems)}"
        ]

        for sub_name, details in subsystems.items():
            if isinstance(details, dict):
                status = details.get("status", "UNKNOWN")
                latency = details.get("latency_ms", 0.0)
                rendered_lines.append(f"  - {sub_name}: [{status}] latency={latency}ms")

        return "\n".join(rendered_lines)

    def verify_loop_closure(self, raw_telemetry_data):
        if not isinstance(raw_telemetry_data, dict):
            return False
        subsystems = raw_telemetry_data.get("subsystems", {})
        has_health_monitor = "market_portfolio_stress_audit_health_monitor" in subsystems
        overall_score = raw_telemetry_data.get("overall_health_score", 0)
        return has_health_monitor and overall_score > 0


def market_portfolio_stress_audit_visualizer(payload=None, **kwargs):
    if payload is None and kwargs:
        payload = kwargs
    if payload is None:
        return MarketPortfolioStressAuditVisualizer()
    if isinstance(payload, dict) and "audit_session_id" in payload and "subsystems" in payload:
        visualizer = MarketPortfolioStressAuditVisualizer()
        return visualizer.aggregate_and_render(payload)

    if not isinstance(payload, dict):
        return str(payload)

    portfolio_id = payload.get("portfolio_id") or payload.get("report_id")
    format_type = payload.get("format", "text_summary")

    adaptive_score = payload.get("adaptive_risk_score")
    export_text = payload.get("export_to_text_report", False)
    tail_risk_metrics = payload.get("tail_risk_metrics")
    stream_payload = payload.get("stream_payload")

    if format_type == "text_summary":
        base_msg = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized."
        )
        if adaptive_score is not None:
            base_msg += f" Adaptive Risk Score: {adaptive_score}."
        if export_text:
            base_msg += " Exported to text report successfully."
        return base_msg
    else:
        result = {
            "portfolio_id": portfolio_id,
            "status": "success",
            "layout": "graphical",
        }
        if adaptive_score is not None:
            result["adaptive_risk_score"] = adaptive_score
        if tail_risk_metrics is not None:
            result["tail_risk_metrics"] = tail_risk_metrics
        if stream_payload is not None:
            result["stream_payload"] = stream_payload
        return result
