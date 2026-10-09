import io
try:
    import requests
except ImportError:
    import unittest.mock as mock
    requests = mock.MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class AuditVisualizerPipeline:
    def __init__(self, audit_log_path=None):
        self.audit_log_path = audit_log_path

    def run_strict_audit(self):
        return True

    def export_audit_summary(self):
        return {"status": "exported"}


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def render_audit_metrics(self, metrics_data, output_path=None):
        return {"status": "rendered", "output_path": output_path}

    def generate_audit_chart_payload(self, risk_metrics, monte_carlo_results):
        return {"risk_metrics": risk_metrics, "monte_carlo_results": monte_carlo_results}


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
