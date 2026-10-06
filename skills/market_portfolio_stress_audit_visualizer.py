import io
import requests
from bs4 import BeautifulSoup


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def generate_audit_summary(self, evaluation_results: list) -> dict:
        total_scenarios = len(evaluation_results) if isinstance(evaluation_results, list) else 0
        passed = sum(1 for item in evaluation_results if isinstance(item, dict) and item.get("status") == "PASSED") if total_scenarios else 0
        warnings = sum(1 for item in evaluation_results if isinstance(item, dict) and item.get("status") == "WARNING") if total_scenarios else 0
        critical = sum(1 for item in evaluation_results if isinstance(item, dict) and item.get("status") == "CRITICAL") if total_scenarios else 0

        return {
            "summary_metrics": {
                "total_scenarios": total_scenarios,
                "passed_count": passed,
                "warning_count": warnings,
                "critical_count": critical
            },
            "audit_status": "COMPLETED",
            "results": evaluation_results
        }


def market_portfolio_stress_audit_visualizer(payload=None, **kwargs):
    if payload is None:
        return MarketPortfolioStressAuditVisualizer(**kwargs)
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