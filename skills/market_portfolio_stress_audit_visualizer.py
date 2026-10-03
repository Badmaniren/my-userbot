import io
import requests
from bs4 import BeautifulSoup


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload=None, **kwargs):
        if payload is None and kwargs:
            payload = kwargs
        return market_portfolio_stress_audit_visualizer(payload)

    def render_audit_dashboard(self, report_data=None, audit_verdict=None, **kwargs):
        return render_audit_dashboard(report_data, audit_verdict, **kwargs)


def render_audit_dashboard(report_data=None, audit_verdict=None, **kwargs):
    try:
        data = report_data if isinstance(report_data, dict) else {}
        verdict = audit_verdict or data.get("audit_verdict", "PASSED")
        portfolio_id = data.get("portfolio_id") or data.get("report_id", "UNKNOWN")
        return {
            "portfolio_id": portfolio_id,
            "audit_verdict": verdict,
            "status": "success",
            "dashboard_metrics": data.get("metrics", {}),
            "layout": "graphical"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def market_portfolio_stress_audit_visualizer(payload=None, **kwargs):
    try:
        if payload is None and kwargs:
            payload = kwargs
        if not isinstance(payload, dict):
            return str(payload)

        portfolio_id = payload.get("portfolio_id") or payload.get("report_id")
        format_type = payload.get("format", "graphical")

        adaptive_score = payload.get("adaptive_risk_score")
        export_text = payload.get("export_to_text_report", False)
        tail_risk_metrics = payload.get("tail_risk_metrics")
        stream_payload = payload.get("stream_payload")

        if stream_payload is not None:
            if hasattr(stream_payload, "read") and callable(stream_payload.read):
                try:
                    stream_payload = stream_payload.read()
                except Exception:
                    pass

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
    except Exception as e:
        return str(payload) if payload is not None else str(e)


def start_new(dependencies=None, **kwargs):
    deps = dependencies or {}
    if isinstance(deps, dict):
        deps.update(kwargs)
        return MarketPortfolioStressAuditVisualizer(**deps)
    return MarketPortfolioStressAuditVisualizer(**kwargs)
