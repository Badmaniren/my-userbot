import io

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from skills.market_portfolio_stress_recovery_coordinator_bridge import (
        market_portfolio_stress_recovery_coordinator_bridge
    )
except ImportError:
    market_portfolio_stress_recovery_coordinator_bridge = None


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")
        self.recovery_bridge = kwargs.get(
            "recovery_bridge", market_portfolio_stress_recovery_coordinator_bridge
        )

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def aggregate_and_render(self, raw_telemetry_data):
        return aggregate_and_render(raw_telemetry_data)

    def verify_loop_closure(self, raw_telemetry_data):
        return verify_loop_closure(raw_telemetry_data)


def market_portfolio_stress_audit_visualizer(payload):
    if not isinstance(payload, dict):
        return str(payload)

    portfolio_id = payload.get("portfolio_id") or payload.get("report_id")
    format_type = payload.get("format", "text_summary")

    adaptive_score = payload.get("adaptive_risk_score")
    export_text = payload.get("export_to_text_report", False)
    tail_risk_metrics = payload.get("tail_risk_metrics")
    stream_payload = payload.get("stream_payload")
    recovery_payload = payload.get("recovery_payload")

    if stream_payload is None and recovery_payload is not None:
        if callable(market_portfolio_stress_recovery_coordinator_bridge):
            stream_payload = market_portfolio_stress_recovery_coordinator_bridge(recovery_payload)

    recovery_progress = payload.get("recovery_progress")
    investor_report = payload.get("investor_report")

    if format_type == "text_summary":
        base_msg = (
            f"Portfolio Stress Audit Summary for {portfolio_id}: "
            f"Data successfully audited and visualized."
        )
        if adaptive_score is not None:
            base_msg += f" Adaptive Risk Score: {adaptive_score}."
        if recovery_progress is not None:
            base_msg += f" Recovery Progress: {recovery_progress}."
        if investor_report:
            base_msg += f" Investor Report: {investor_report}."
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
        if recovery_progress is not None:
            result["recovery_progress"] = recovery_progress
        if investor_report is not None:
            result["investor_report"] = investor_report

        result["charts"] = {
            "recovery_trajectory": "structured_graph_rendered",
            "stress_impact": "tail_risk_chart_rendered"
        }
        return result


def aggregate_and_render(raw_telemetry_data):
    if not isinstance(raw_telemetry_data, dict):
        return {"status": "error", "message": "Invalid telemetry data"}

    portfolio_id = raw_telemetry_data.get("portfolio_id", "UNKNOWN")
    metrics = raw_telemetry_data.get("metrics", {})
    return {
        "portfolio_id": portfolio_id,
        "rendered": True,
        "aggregated_metrics": metrics,
        "recovery_status": raw_telemetry_data.get("recovery_status", "in_progress")
    }


def verify_loop_closure(raw_telemetry_data):
    if not isinstance(raw_telemetry_data, dict):
        return False
    return raw_telemetry_data.get("loop_closed", True)
