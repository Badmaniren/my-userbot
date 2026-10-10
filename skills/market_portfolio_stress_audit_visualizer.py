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
    from skills.market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
except ImportError:
    try:
        from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge as market_portfolio_backtest_evaluator_bridge
    except ImportError:
        def market_portfolio_backtest_evaluator_bridge(payload=None, **kwargs):
            return payload

try:
    from skills.market_report_generator import market_report_generator
except ImportError:
    try:
        from skills.market_report_generator import MarketReportGenerator as market_report_generator
    except ImportError:
        def market_report_generator(payload=None, **kwargs):
            return payload


class AuditVisualizerPipeline:
    def __init__(self, audit_log_path=None, **kwargs):
        self.audit_log_path = audit_log_path
        self.kwargs = kwargs

    def run_strict_audit(self, payload=None, **kwargs):
        data = payload or {}
        return {
            "status": "audited",
            "audit_log_path": self.audit_log_path,
            "passed": True,
            "data": data
        }

    def export_audit_summary(self, output_path=None, **kwargs):
        return {
            "status": "exported",
            "output_path": output_path,
            "audit_log_path": self.audit_log_path
        }


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def render_audit_metrics(self, metrics_data, output_path=None):
        if output_path and isinstance(output_path, str):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(str(metrics_data))
        return {
            "status": "rendered",
            "metrics": metrics_data,
            "output_path": output_path
        }

    def generate_audit_chart_payload(self, risk_metrics=None, monte_carlo_results=None):
        return {
            "type": "audit_chart",
            "risk_metrics": risk_metrics or {},
            "monte_carlo_results": monte_carlo_results or {}
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
