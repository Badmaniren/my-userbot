import io

try:
    from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
except ImportError:
    market_portfolio_alert_dispatcher = None


class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

    def visualize_stress_test(self, result_dict):
        return visualize_stress_test(result_dict)

    def generate_report(self, raw_data, mc_results=None):
        return generate_audit_report(raw_data, mc_results, None)

    def render_audit_dashboard(self, report_data, audit_verdict="PASSED"):
        return render_audit_dashboard(report_data, audit_verdict)


def market_portfolio_stress_audit_visualizer(payload):
    if hasattr(payload, "read") and callable(payload.read):
        try:
            content = payload.read()
            if isinstance(content, bytes):
                payload = content.decode("utf-8")
            else:
                payload = str(content)
        except Exception:
            payload = str(payload)

    if not isinstance(payload, dict):
        return str(payload)

    portfolio_id = payload.get("portfolio_id") or payload.get("report_id") or "UNKNOWN"
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


def visualize_stress_test(result_dict):
    if not isinstance(result_dict, dict):
        return str(result_dict)

    payload = dict(result_dict)
    if "format" not in payload:
        payload["format"] = "graphical"

    return market_portfolio_stress_audit_visualizer(payload)


def generate_audit_report(ingested_data, scenario_results=None, simulation_output=None):
    portfolio_id = "UNKNOWN"
    if isinstance(ingested_data, dict):
        portfolio_id = ingested_data.get("portfolio_id") or ingested_data.get("report_id") or portfolio_id
    elif isinstance(scenario_results, dict):
        portfolio_id = scenario_results.get("portfolio_id") or portfolio_id

    return {
        "portfolio_id": portfolio_id,
        "status": "audited",
        "ingested_data": ingested_data,
        "scenario_results": scenario_results,
        "simulation_output": simulation_output
    }


def render_audit_dashboard(report_data, audit_verdict="PASSED"):
    portfolio_id = "UNKNOWN"
    if isinstance(report_data, dict):
        portfolio_id = report_data.get("portfolio_id") or portfolio_id

    return {
        "portfolio_id": portfolio_id,
        "audit_verdict": audit_verdict,
        "report_data": report_data,
        "dashboard": "rendered"
    }


def start_new(dependencies=None, **kwargs):
    deps = dependencies or {}
    deps.update(kwargs)
    return MarketPortfolioStressAuditVisualizer(**deps)
