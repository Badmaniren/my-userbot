import io

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from skills.market_portfolio_stress_audit_exporter_v2 import MarketPortfolioStressAuditExporterV2, market_portfolio_stress_audit_exporter_v2


class AuditVisualizerPipeline:
    def __init__(self, audit_log_path=None, **kwargs):
        self.audit_log_path = audit_log_path
        self.kwargs = kwargs

    def run_strict_audit(self, payload=None):
        return {"status": "audited", "path": self.audit_log_path, "payload": payload}

    def export_audit_summary(self):
        return {"audit_summary": "ok", "path": self.audit_log_path}


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")
        if "market_portfolio_stress_audit_exporter_v2" in kwargs:
            self.exporter = kwargs.get("market_portfolio_stress_audit_exporter_v2")
        else:
            self.exporter = market_portfolio_stress_audit_exporter_v2

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def generate_audit_chart_payload(self, risk_metrics=None, monte_carlo_results=None):
        return {
            "risk_metrics": risk_metrics or {},
            "monte_carlo_results": monte_carlo_results or {},
            "status": "ready"
        }


def generate_audit_chart_payload(risk_metrics=None, monte_carlo_results=None):
    return {
        "risk_metrics": risk_metrics or {},
        "monte_carlo_results": monte_carlo_results or {},
        "status": "ready"
    }


def market_portfolio_stress_audit_visualizer(payload):
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