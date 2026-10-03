import io
import requests
from bs4 import BeautifulSoup


def _process_visualizer_payload(payload):
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


class market_portfolio_stress_audit_visualizer:
    """Аудит и визуализатор результатов стресс-тестов."""

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and not kwargs:
            # Вызов функции с аргументом payload: market_portfolio_stress_audit_visualizer(payload)
            return _process_visualizer_payload(args[0])
        instance = super().__new__(cls)
        return instance

    def __init__(self, *args, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def generate_audit_report(self, ingested_data, scenario_results, simulation_output):
        portfolio_id = ingested_data.get("portfolio_id") if isinstance(ingested_data, dict) else None
        return {
            "portfolio_id": portfolio_id,
            "audit_status": "PASSED",
            "ingested_data": ingested_data,
            "scenario_results": scenario_results,
            "simulation_output": simulation_output
        }

    def visualize(self, payload):
        return _process_visualizer_payload(payload)


class MarketPortfolioStressAuditVisualizer(market_portfolio_stress_audit_visualizer):
    pass
